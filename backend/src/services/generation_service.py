import os
import asyncio
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException

CONCURRENCY = int(os.getenv("LLM_CONCURRENCY", "5"))

from backend.src.models import (
    Project, SourceDocument, GeneratedDocument, GenerationJob,
    DocumentStatus, JobStatus, DocCode
)
from backend.src.utils.file_parser import parse_document
from backend.src.utils.doc_extractor import extract_content
from backend.src.services.llm_client import call_llm
from backend.src.services.normaliser import (
    normalise_sap, normalise_pra, normalise_rtm,
    normalise_stp, normalise_utr, normalise_asr
)
from backend.src.services.output_renderer import render_document
from backend.src.services.rag_service import build_all_context_packages
from backend.src.services.output_validator import validate_and_correct
from backend.src.prompts.requirement_context import ProjectMetadata
from backend.src.prompts.sap_prompt import build_sap_prompt
from backend.src.prompts.pra_prompt import build_pra_prompt
from backend.src.prompts.rtm_prompt import build_rtm_prompt
from backend.src.prompts.stp_prompt import build_stp_prompt, build_stp_system_prompt, build_stp_user_prompt
from backend.src.prompts.utr_prompt import build_utr_prompt, build_utr_system_prompt, build_utr_user_prompt
from backend.src.prompts.asr_prompt import build_asr_prompt


def _get_source_text(project_id: str, doc_type: str, db: Session) -> str:
    record = db.query(SourceDocument).filter(
        SourceDocument.project_id == project_id,
        SourceDocument.doc_type == doc_type
    ).first()
    if not record:
        return ""
    with open(record.file_path, "rb") as f:
        content = f.read()
    ext = "." + record.file_name.rsplit(".", 1)[-1].lower()
    return parse_document(content, ext)


def _get_generated_content(project_id: str, doc_code: str, db: Session) -> dict:
    record = db.query(GeneratedDocument).filter(
        GeneratedDocument.project_id == project_id,
        GeneratedDocument.doc_code == doc_code
    ).first()
    if not record or not record.generated_content:
        raise HTTPException(status_code=400, detail=f"{doc_code} content not found. Ensure {doc_code} HITL is complete.")
    return record.generated_content


def _create_or_reset_doc(project_id: str, doc_code: str, db: Session) -> GeneratedDocument:
    record = db.query(GeneratedDocument).filter(
        GeneratedDocument.project_id == project_id,
        GeneratedDocument.doc_code == doc_code
    ).first()
    if record:
        record.status = DocumentStatus.GENERATING
        record.ai_pdf_path = None
        record.word_path = None
        record.generated_content = None
        record.generated_at = None
    else:
        record = GeneratedDocument(
            project_id=project_id,
            doc_code=doc_code,
            status=DocumentStatus.GENERATING
        )
        db.add(record)
    db.commit()
    db.refresh(record)
    return record


def _create_job(project_id: str, doc_code: str, db: Session) -> GenerationJob:
    job = GenerationJob(
        project_id=project_id,
        doc_code=doc_code,
        status=JobStatus.IN_PROGRESS,
        started_at=datetime.now(timezone.utc)
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def _complete_job(job: GenerationJob, db: Session) -> None:
    job.status = JobStatus.COMPLETE
    job.completed_at = datetime.now(timezone.utc)
    db.commit()


def _fail_job(job: GenerationJob, error: str, db: Session) -> None:
    job.status = JobStatus.FAILED
    job.error_message = error
    job.completed_at = datetime.now(timezone.utc)
    db.commit()


def _get_completed_req_ids(project_id: str, doc_code: str, db: Session) -> set[str]:
    record = db.query(GeneratedDocument).filter(
        GeneratedDocument.project_id == project_id,
        GeneratedDocument.doc_code == doc_code,
        GeneratedDocument.status == DocumentStatus.AI_COMPLETE,
    ).first()
    if not record or not record.generated_content:
        return set()
    key = "test_cases" if doc_code == "STP" else "test_records"
    items = record.generated_content.get(key, [])
    return {item.get("req_id") for item in items if item.get("req_id")}


async def _generate_cases_per_requirement(
    ctx_packages: list,
    doc_type: str,
    metadata: ProjectMetadata,
    valid_req_ids: list[str],
    job=None,
    db=None,
) -> list[dict]:
    if doc_type == "STP":
        system_prompt = build_stp_system_prompt(metadata)
        build_user = build_stp_user_prompt
        id_prefix, id_field = "TC", "tc_id"
    else:
        system_prompt = build_utr_system_prompt(metadata)
        build_user = build_utr_user_prompt
        id_prefix, id_field = "UTR", "utr_id"

    semaphore = asyncio.Semaphore(CONCURRENCY)
    results = [None] * len(ctx_packages)

    async def _process_one(idx: int, ctx):
        async with semaphore:
            user_prompt = build_user(ctx)
            try:
                raw = await call_llm(user_prompt, system_prompt)
            except HTTPException:
                results[idx] = {
                    id_field: f"{id_prefix}-{idx + 1:03d}",
                    "req_id": ctx.req_id,
                    "confidence": "Low",
                    "flags": ["VALIDATION_FAILED", "LLM_CALL_FAILED"],
                }
                if job and db:
                    job.completed_requirements = (job.completed_requirements or 0) + 1
                    db.commit()
                return

            items = raw if isinstance(raw, list) else [raw]
            validated_items = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                item[id_field] = f"{id_prefix}-{idx + 1:03d}"
                validated = await validate_and_correct(
                    item, doc_type, valid_req_ids, ctx.risk_classification, system_prompt
                )
                validated_items.append(validated)

            results[idx] = validated_items[0] if len(validated_items) == 1 else validated_items

            if job and db:
                job.completed_requirements = (job.completed_requirements or 0) + 1
                db.commit()

    await asyncio.gather(*[_process_one(i, ctx) for i, ctx in enumerate(ctx_packages)])

    # Flatten multi-AC results and assign sequential IDs
    collected = []
    counter = 1
    for r in results:
        if r is None:
            continue
        items = r if isinstance(r, list) else [r]
        for item in items:
            item[id_field] = f"{id_prefix}-{counter:03d}"
            collected.append(item)
            counter += 1

    return collected


async def generate_sap(project_id: str, system_type: str, db: Session) -> GeneratedDocument:
    doc_record = _create_or_reset_doc(project_id, DocCode.SAP, db)
    job = _create_job(project_id, DocCode.SAP, db)
    try:
        urs_text = _get_source_text(project_id, "URS", db)
        frs_text = _get_source_text(project_id, "FRS", db)
        brd_text = _get_source_text(project_id, "BRD", db)

        extracted = extract_content(urs_text, frs_text, brd_text)
        prompt = build_sap_prompt(extracted, system_type, project_id)
        raw = await call_llm(prompt)
        normalised = normalise_sap(raw)

        word_path, pdf_path = render_document(DocCode.SAP, normalised, project_id, system_type)

        doc_record.status = DocumentStatus.AI_COMPLETE
        doc_record.word_path = word_path
        doc_record.ai_pdf_path = pdf_path
        doc_record.generated_content = normalised
        doc_record.generated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(doc_record)
        _complete_job(job, db)
        return doc_record
    except Exception as e:
        _fail_job(job, str(e), db)
        raise


async def generate_pra(project_id: str, system_type: str, db: Session) -> GeneratedDocument:
    doc_record = _create_or_reset_doc(project_id, DocCode.PRA, db)
    job = _create_job(project_id, DocCode.PRA, db)
    try:
        sap_content = _get_generated_content(project_id, DocCode.SAP, db)
        intended_uses = sap_content.get("intended_uses", [])

        prompt = build_pra_prompt(intended_uses, system_type, project_id)
        raw = await call_llm(prompt)
        normalised = normalise_pra(raw)

        word_path, pdf_path = render_document(DocCode.PRA, normalised, project_id, system_type)

        doc_record.status = DocumentStatus.AI_COMPLETE
        doc_record.word_path = word_path
        doc_record.ai_pdf_path = pdf_path
        doc_record.generated_content = normalised
        doc_record.generated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(doc_record)
        _complete_job(job, db)
        return doc_record
    except Exception as e:
        _fail_job(job, str(e), db)
        raise


async def generate_rtm_stp_utr(project_id: str, db: Session) -> list[GeneratedDocument]:
    sap_content = _get_generated_content(project_id, DocCode.SAP, db)
    pra_content = _get_generated_content(project_id, DocCode.PRA, db)

    urs_text = _get_source_text(project_id, "URS", db)
    frs_text = _get_source_text(project_id, "FRS", db)
    brd_text = _get_source_text(project_id, "BRD", db)

    project = db.query(Project).filter(Project.id == project_id).first()
    metadata = ProjectMetadata(
        project_id=project_id,
        system_name=project.name if project else project_id,
        system_type=project.system_type if project else "LIMS",
    )

    # RAG: build one context package per requirement
    ctx_packages = build_all_context_packages(
        urs_text, frs_text, brd_text, sap_content, pra_content, metadata
    )
    valid_req_ids = [p.req_id for p in ctx_packages]

    high_risk_pkgs = [p for p in ctx_packages if p.risk_classification == "High Process Risk"]
    not_high_pkgs = [p for p in ctx_packages if p.risk_classification != "High Process Risk"]

    # RTM — single document-level call (unchanged from pre-Sprint 1)
    extracted = extract_content(urs_text, frs_text, brd_text)
    risk_classifications = pra_content.get("risk_classifications", [])

    results = []

    rtm_record = _create_or_reset_doc(project_id, DocCode.RTM, db)
    rtm_job = _create_job(project_id, DocCode.RTM, db)
    try:
        raw = await call_llm(build_rtm_prompt(extracted, risk_classifications, project_id))
        word_path, pdf_path = render_document(DocCode.RTM, raw, project_id)
        rtm_record.status = DocumentStatus.AI_COMPLETE
        rtm_record.word_path = word_path
        rtm_record.ai_pdf_path = pdf_path
        rtm_record.generated_content = raw
        rtm_record.generated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(rtm_record)
        _complete_job(rtm_job, db)
        results.append(rtm_record)
    except Exception as e:
        _fail_job(rtm_job, str(e), db)
        raise

    # STP — parallel per-requirement calls with resume support
    stp_record = _create_or_reset_doc(project_id, DocCode.STP, db)
    stp_job = _create_job(project_id, DocCode.STP, db)
    try:
        completed_stp_ids = _get_completed_req_ids(project_id, DocCode.STP, db)
        pending_stp_pkgs = [p for p in high_risk_pkgs if p.req_id not in completed_stp_ids]
        stp_job.total_requirements = len(pending_stp_pkgs)
        db.commit()
        test_cases = await _generate_cases_per_requirement(
            pending_stp_pkgs, "STP", metadata, valid_req_ids, job=stp_job, db=db
        )
        normalised = normalise_stp({"test_cases": test_cases})
        word_path, pdf_path = render_document(DocCode.STP, normalised, project_id)
        stp_record.status = DocumentStatus.AI_COMPLETE
        stp_record.word_path = word_path
        stp_record.ai_pdf_path = pdf_path
        stp_record.generated_content = normalised
        stp_record.generated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(stp_record)
        _complete_job(stp_job, db)
        results.append(stp_record)
    except Exception as e:
        _fail_job(stp_job, str(e), db)
        raise

    # UTR — parallel per-requirement calls with resume support
    utr_record = _create_or_reset_doc(project_id, DocCode.UTR, db)
    utr_job = _create_job(project_id, DocCode.UTR, db)
    try:
        completed_utr_ids = _get_completed_req_ids(project_id, DocCode.UTR, db)
        pending_utr_pkgs = [p for p in not_high_pkgs if p.req_id not in completed_utr_ids]
        utr_job.total_requirements = len(pending_utr_pkgs)
        db.commit()
        test_records = await _generate_cases_per_requirement(
            pending_utr_pkgs, "UTR", metadata, valid_req_ids, job=utr_job, db=db
        )
        normalised = normalise_utr({"test_records": test_records})
        word_path, pdf_path = render_document(DocCode.UTR, normalised, project_id)
        utr_record.status = DocumentStatus.AI_COMPLETE
        utr_record.word_path = word_path
        utr_record.ai_pdf_path = pdf_path
        utr_record.generated_content = normalised
        utr_record.generated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(utr_record)
        _complete_job(utr_job, db)
        results.append(utr_record)
    except Exception as e:
        _fail_job(utr_job, str(e), db)
        raise

    return results


async def generate_asr(project_id: str, db: Session) -> GeneratedDocument:
    doc_record = _create_or_reset_doc(project_id, DocCode.ASR, db)
    job = _create_job(project_id, DocCode.ASR, db)
    try:
        sap_content = _get_generated_content(project_id, DocCode.SAP, db)
        pra_content = _get_generated_content(project_id, DocCode.PRA, db)
        stp_content = _get_generated_content(project_id, DocCode.STP, db)
        utr_content = _get_generated_content(project_id, DocCode.UTR, db)

        prompt = build_asr_prompt(
            intended_uses=sap_content.get("intended_uses", []),
            risk_classifications=pra_content.get("risk_classifications", []),
            test_cases=stp_content.get("test_cases", []),
            test_records=utr_content.get("test_records", []),
            project_id=project_id
        )
        raw = await call_llm(prompt)
        normalised = normalise_asr(raw)

        word_path, pdf_path = render_document(DocCode.ASR, normalised, project_id)

        doc_record.status = DocumentStatus.AI_COMPLETE
        doc_record.word_path = word_path
        doc_record.ai_pdf_path = pdf_path
        doc_record.generated_content = normalised
        doc_record.generated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(doc_record)
        _complete_job(job, db)
        return doc_record
    except Exception as e:
        _fail_job(job, str(e), db)
        raise
