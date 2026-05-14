import os
import aiofiles

STORAGE_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..", "storage")


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def get_project_dir(project_id: str) -> str:
    path = os.path.join(STORAGE_ROOT, project_id)
    _ensure_dir(path)
    return path


def source_file_path(project_id: str, doc_type: str, ext: str) -> str:
    directory = get_project_dir(project_id)
    return os.path.join(directory, f"{doc_type}{ext}")


def ai_pdf_path(project_id: str, doc_code: str) -> str:
    directory = get_project_dir(project_id)
    return os.path.join(directory, f"{doc_code}-AI-{project_id}.pdf")


def word_review_path(project_id: str, doc_code: str) -> str:
    directory = get_project_dir(project_id)
    return os.path.join(directory, f"{doc_code}-REVIEW-{project_id}.docx")


def hitl_pdf_path(project_id: str, doc_code: str) -> str:
    directory = get_project_dir(project_id)
    return os.path.join(directory, f"{doc_code}-HITL-{project_id}.pdf")


def stp_exec_word_path(project_id: str) -> str:
    directory = get_project_dir(project_id)
    return os.path.join(directory, f"STP-EXEC-{project_id}.docx")


def stp_exec_hitl_pdf_path(project_id: str) -> str:
    directory = get_project_dir(project_id)
    return os.path.join(directory, f"STP-EXEC-HITL-{project_id}.pdf")


def zip_package_path(project_id: str) -> str:
    directory = get_project_dir(project_id)
    return os.path.join(directory, f"{project_id}_Validation_Package_Complete.zip")


async def save_file(path: str, content: bytes) -> None:
    async with aiofiles.open(path, "wb") as f:
        await f.write(content)
