from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException

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
from backend.src.prompts.sap_prompt import build_sap_prompt
from backend.src.prompts.pra_prompt import build_pra_prompt
from backend.src.prompts.rtm_prompt import build_rtm_prompt
from backend.src.prompts.stp_prompt import build_stp_prompt
from backend.src.prompts.utr_prompt import build_utr_prompt
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
    frs_text = _get_source_text(project_id, "FRS", db)

    urs_text = _get_source_text(project_id, "URS", db)
    brd_text = _get_source_text(project_id, "BRD", db)
    extracted = extract_content(urs_text, frs_text, brd_text)

    risk_classifications = pra_content.get("risk_classifications", [])
    high_risk = [r for r in risk_classifications if "Not High" not in r.get("risk_classification", "")]
    not_high_risk = [r for r in risk_classifications if "Not High" in r.get("risk_classification", "")]

    results = []
    for doc_code, prompt_fn, normalise_fn, extra in [
        (DocCode.RTM, lambda: build_rtm_prompt(extracted, risk_classifications, project_id), lambda r: r, {}),
        (DocCode.STP, lambda: build_stp_prompt(high_risk, frs_text, project_id), lambda r: r, {}),
        (DocCode.UTR, lambda: build_utr_prompt(not_high_risk, frs_text, project_id), lambda r: r, {}),
    ]:
        doc_record = _create_or_reset_doc(project_id, doc_code, db)
        job = _create_job(project_id, doc_code, db)
        try:
            raw = await call_llm(prompt_fn())
            normalised = normalise_fn(raw)
            word_path, pdf_path = render_document(doc_code, normalised, project_id)
            doc_record.status = DocumentStatus.AI_COMPLETE
            doc_record.word_path = word_path
            doc_record.ai_pdf_path = pdf_path
            doc_record.generated_content = normalised
            doc_record.generated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(doc_record)
            _complete_job(job, db)
            results.append(doc_record)
        except Exception as e:
            _fail_job(job, str(e), db)
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
