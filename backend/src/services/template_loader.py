import os
import shutil
from fastapi import HTTPException

TEMPLATES_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "docs", "templates"
)

TEMPLATE_MAP = {
    "SAP": "Template_v11_Doc1_SAP.docx",
    "PRA": "Template_v11_Doc2_PRA.docx",
    "RTM": "Template_v11_Doc3_RTM.docx",
    "STP": "Template_v11_Doc4_STP.docx",
    "UTR": "Template_v11_Doc5_UTR.docx",
    "ASR": "Template_v11_Doc6_ASR.docx",
}


def get_template_path(doc_code: str) -> str:
    filename = TEMPLATE_MAP.get(doc_code)
    if not filename:
        raise HTTPException(status_code=500, detail=f"No template found for document: {doc_code}")
    path = os.path.join(TEMPLATES_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=500, detail=f"Template file missing: {filename}")
    return path


def copy_template_to(doc_code: str, destination: str) -> None:
    source = get_template_path(doc_code)
    shutil.copy2(source, destination)
