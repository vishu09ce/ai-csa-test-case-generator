import os
import pytest
from unittest.mock import patch

from backend.src.models import DocCode, ProjectState
from backend.src.utils import file_store


@pytest.fixture(autouse=True)
def tmp_storage(tmp_path):
    with patch.object(file_store, "STORAGE_ROOT", str(tmp_path)):
        yield


@pytest.mark.parametrize("doc_code", list(DocCode))
def test_generated_file_names_use_plain_doc_code(doc_code):
    # The frontend downloads e.g. "SAP-AI-<id>.pdf"; enum members must not
    # render as "DocCode.SAP" in file names.
    assert os.path.basename(file_store.ai_pdf_path("PROJ-X", doc_code)) == f"{doc_code.value}-AI-PROJ-X.pdf"
    assert os.path.basename(file_store.word_review_path("PROJ-X", doc_code)) == f"{doc_code.value}-REVIEW-PROJ-X.docx"
    assert os.path.basename(file_store.hitl_pdf_path("PROJ-X", doc_code)) == f"{doc_code.value}-HITL-PROJ-X.pdf"


def test_enums_format_as_plain_values():
    assert f"{DocCode.SAP}" == "SAP"
    assert f"{ProjectState.PRA_REVIEW}" == "PRA_REVIEW"
