import asyncio
import pytest
import time
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException

from backend.src.services.generation_service import (
    _generate_cases_per_requirement,
    _get_completed_req_ids,
    CONCURRENCY,
)
from backend.src.models import GeneratedDocument, DocumentStatus, DocCode


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

class _FakeCtx:
    """Minimal stand-in for a RAG context package."""

    def __init__(self, req_id: str, risk: str = "High Process Risk"):
        self.req_id = req_id
        self.risk_classification = risk


FAKE_METADATA = MagicMock()

GOOD_STP_ITEM = {
    "tc_id": "TC-001",
    "req_id": "URS-001",
    "title": "Verify login",
    "objective": "Ensure login works",
    "preconditions": "User exists",
    "steps": [{"step_number": 1, "action": "Login", "expected_result": "Dashboard shown"}],
    "acceptance_criteria": "Login succeeds",
    "confidence": "High",
    "flags": [],
}


def _make_pkgs(n: int) -> list[_FakeCtx]:
    return [_FakeCtx(f"URS-{i:03d}") for i in range(1, n + 1)]


# ---------------------------------------------------------------------------
# B2 — Backoff tests (testing call_llm directly)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_backoff_retries_on_429_and_succeeds():
    """call_llm should retry twice on 429 then return successfully."""
    call_count = 0

    async def fake_acompletion(**kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise Exception("Error 429 rate_limit exceeded")
        resp = MagicMock()
        resp.choices[0].message.content = '{"tc_id": "TC-001"}'
        return resp

    with patch("backend.src.services.llm_client.litellm.acompletion", side_effect=fake_acompletion), \
         patch("backend.src.services.llm_client.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        from backend.src.services.llm_client import call_llm
        result = await call_llm("test prompt")

    assert result == {"tc_id": "TC-001"}
    assert call_count == 3
    assert mock_sleep.call_count == 2


@pytest.mark.asyncio
async def test_backoff_fails_after_max_retries():
    """call_llm should raise HTTPException after exhausting all 3 attempts on 429."""
    async def always_429(**kwargs):
        raise Exception("HTTP 429 rate_limit")

    with patch("backend.src.services.llm_client.litellm.acompletion", side_effect=always_429), \
         patch("backend.src.services.llm_client.asyncio.sleep", new_callable=AsyncMock):
        from backend.src.services.llm_client import call_llm
        with pytest.raises(HTTPException) as exc_info:
            await call_llm("test prompt")

    assert exc_info.value.status_code == 500


# ---------------------------------------------------------------------------
# B3 — Parallel execution tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_semaphore_limits_concurrency():
    """No more than CONCURRENCY calls should overlap at the same time."""
    pkgs = _make_pkgs(10)
    active = []
    peak = [0]

    async def fake_call_llm(prompt, system_prompt=None):
        active.append(1)
        peak[0] = max(peak[0], len(active))
        await asyncio.sleep(0.05)
        active.pop()
        return {
            "tc_id": "TC-001",
            "req_id": "URS-001",
            "title": "T",
            "objective": "O",
            "preconditions": "P",
            "steps": [{"step_number": 1, "action": "A", "expected_result": "R"}],
            "acceptance_criteria": "AC",
            "confidence": "High",
            "flags": [],
        }

    async def fake_validate(item, *args, **kwargs):
        return item

    with patch("backend.src.services.generation_service.call_llm", side_effect=fake_call_llm), \
         patch("backend.src.services.generation_service.validate_and_correct", side_effect=fake_validate), \
         patch("backend.src.services.generation_service.build_stp_system_prompt", return_value="sys"), \
         patch("backend.src.services.generation_service.build_stp_user_prompt", return_value="user"):
        await _generate_cases_per_requirement(pkgs, "STP", FAKE_METADATA, [p.req_id for p in pkgs])

    assert peak[0] <= CONCURRENCY


@pytest.mark.asyncio
async def test_parallel_results_ordered_correctly():
    """TC IDs must be sequential TC-001 to TC-005 regardless of completion order."""
    pkgs = _make_pkgs(5)

    async def fake_call_llm(prompt, system_prompt=None):
        await asyncio.sleep(0.01)
        return {
            "tc_id": "TC-001",
            "req_id": "URS-001",
            "title": "T",
            "objective": "O",
            "preconditions": "P",
            "steps": [{"step_number": 1, "action": "A", "expected_result": "R"}],
            "acceptance_criteria": "AC",
            "confidence": "High",
            "flags": [],
        }

    async def fake_validate(item, *args, **kwargs):
        return item

    with patch("backend.src.services.generation_service.call_llm", side_effect=fake_call_llm), \
         patch("backend.src.services.generation_service.validate_and_correct", side_effect=fake_validate), \
         patch("backend.src.services.generation_service.build_stp_system_prompt", return_value="sys"), \
         patch("backend.src.services.generation_service.build_stp_user_prompt", return_value="user"):
        results = await _generate_cases_per_requirement(
            pkgs, "STP", FAKE_METADATA, [p.req_id for p in pkgs]
        )

    assert len(results) == 5
    assert [r["tc_id"] for r in results] == ["TC-001", "TC-002", "TC-003", "TC-004", "TC-005"]


@pytest.mark.asyncio
async def test_llm_failure_one_req_does_not_block_others():
    """One HTTPException from call_llm must not stop the rest; 5 results returned."""
    pkgs = _make_pkgs(5)
    call_count = [0]

    async def selective_fail(prompt, system_prompt=None):
        call_count[0] += 1
        if call_count[0] == 3:
            raise HTTPException(status_code=500, detail="LLM call failed")
        return {
            "tc_id": "TC-001",
            "req_id": "URS-001",
            "title": "T",
            "objective": "O",
            "preconditions": "P",
            "steps": [{"step_number": 1, "action": "A", "expected_result": "R"}],
            "acceptance_criteria": "AC",
            "confidence": "High",
            "flags": [],
        }

    async def fake_validate(item, *args, **kwargs):
        return item

    with patch("backend.src.services.generation_service.call_llm", side_effect=selective_fail), \
         patch("backend.src.services.generation_service.validate_and_correct", side_effect=fake_validate), \
         patch("backend.src.services.generation_service.build_stp_system_prompt", return_value="sys"), \
         patch("backend.src.services.generation_service.build_stp_user_prompt", return_value="user"):
        results = await _generate_cases_per_requirement(
            pkgs, "STP", FAKE_METADATA, [p.req_id for p in pkgs]
        )

    assert len(results) == 5
    failed = [r for r in results if "LLM_CALL_FAILED" in r.get("flags", [])]
    assert len(failed) == 1


# ---------------------------------------------------------------------------
# B4 — Resume logic tests
# ---------------------------------------------------------------------------

def test_resume_skips_completed_requirements(db):
    """_get_completed_req_ids returns req_ids from a saved AI_COMPLETE STP record."""
    from backend.src.models import Project

    project = Project(id="proj-resume", name="Resume Test", system_type="LIMS")
    db.add(project)

    doc = GeneratedDocument(
        project_id="proj-resume",
        doc_code=DocCode.STP,
        status=DocumentStatus.AI_COMPLETE,
        generated_content={
            "test_cases": [
                {"tc_id": "TC-001", "req_id": "URS-001"},
                {"tc_id": "TC-002", "req_id": "URS-002"},
            ]
        },
    )
    db.add(doc)
    db.commit()

    completed = _get_completed_req_ids("proj-resume", DocCode.STP, db)
    assert completed == {"URS-001", "URS-002"}

    all_pkgs = _make_pkgs(4)  # URS-001 to URS-004
    pending = [p for p in all_pkgs if p.req_id not in completed]
    assert len(pending) == 2
    assert {p.req_id for p in pending} == {"URS-003", "URS-004"}


# ---------------------------------------------------------------------------
# B5 — Status endpoint progress fields
# ---------------------------------------------------------------------------

def test_status_endpoint_includes_progress_fields(client, project):
    """GET /api/projects/{id}/status must include total_requirements and completed_requirements."""
    resp = client.get(f"/api/projects/{project['id']}/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "active_jobs" in data
    # When no jobs exist the list is empty — verify the key exists
    # When jobs are present each entry must have the progress fields
    for job in data["active_jobs"]:
        assert "total_requirements" in job
        assert "completed_requirements" in job
