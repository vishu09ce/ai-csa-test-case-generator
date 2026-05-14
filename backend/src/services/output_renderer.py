from backend.src.services.word_assembler import (
    assemble_sap, assemble_pra, assemble_rtm,
    assemble_stp, assemble_utr, assemble_asr
)
from backend.src.services.pdf_converter import convert_to_pdf
from backend.src.utils.file_store import word_review_path, ai_pdf_path


ASSEMBLERS = {
    "SAP": assemble_sap,
    "PRA": assemble_pra,
    "RTM": assemble_rtm,
    "STP": assemble_stp,
    "UTR": assemble_utr,
    "ASR": assemble_asr,
}


def render_document(doc_code: str, data: dict, project_id: str, system_type: str = "") -> tuple[str, str]:
    assembler = ASSEMBLERS.get(doc_code)
    if not assembler:
        raise ValueError(f"No assembler found for document: {doc_code}")

    word_path = word_review_path(project_id, doc_code)
    pdf_path = ai_pdf_path(project_id, doc_code)

    if doc_code in ("SAP", "PRA"):
        doc = assembler(data, project_id, system_type)
    else:
        doc = assembler(data, project_id)

    doc.save(word_path)
    convert_to_pdf(word_path, pdf_path)

    return word_path, pdf_path
