import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException

from backend.src.services.generation_service import _generate_cases_per_requirement
from backend.src.prompts.requirement_context import RequirementContext, ProjectMetadata


def _make_ctx(req_id="REQ-001", risk_class="High Process Risk"):
    return RequirementContext(
        req_id=req_id,
        source_document="URS",
        section_heading="3.1 Feature",
        requirement_text=f"The system shall support {req_id}.",
        adjacent_prev=[],
        adjacent_next=[],
        frs_specification="FRS: system assigns unique ID in format SMP-NNN.",
        frs_link_type="explicit",
        acceptance_criteria="AC: ID is unique and matches format SMP-NNN.",
        ac_source="FRS",
        intended_use_statement="Provide sample tracking.",
        iu_ref="IU-001",
        risk_classification=risk_class,
        risk_rationale="Risk rationale.",
    )


METADATA = ProjectMetadata(
    project_id="PROJ-TEST",
    system_name="TrackSure LIMS",
    system_type="LIMS",
)

_VALID_TC = {
    "tc_id": "TC-001",
    "req_id": "REQ-001",
    "iu_ref": "IU-001",
    "risk_class": "High Process Risk",
    "preconditions": ["User is logged in with Admin role"],
    "test_steps": ["Navigate to the sample login page", "Enter sample ID", "Click Submit"],
    "expected_result": "System assigns a unique ID in format SMP-NNN and displays confirmation.",
    "actual_result": "",
    "pass_fail": "",
    "confidence": "High",
    "flags": [],
}

_VALID_UTR = {
    "utr_id": "UTR-001",
    "req_id": "REQ-001",
    "iu_ref": "IU-001",
    "risk_class": "Not High Process Risk",
    "feature_description": "Dashboard summary view showing record counts.",
    "exploratory_scenarios": [
        "Normal use: verify dashboard loads with correct counts.",
        "Boundary condition: verify with zero records.",
        "Error state: verify with network disconnected.",
    ],
    "tester_observations": "",
    "conclusion": "",
    "confidence": "High",
    "flags": [],
}


@pytest.mark.asyncio
class TestGenerateCasesPerRequirement:
    async def test_empty_packages_returns_empty_list(self):
        result = await _generate_cases_per_requirement([], "STP", METADATA, [])
        assert result == []

    async def test_produces_one_stp_per_requirement(self):
        pkgs = [_make_ctx("REQ-001"), _make_ctx("REQ-002")]
        tc1 = {**_VALID_TC, "req_id": "REQ-001", "flags": []}
        tc2 = {**_VALID_TC, "req_id": "REQ-002", "flags": []}

        with patch("backend.src.services.generation_service.call_llm",
                   new=AsyncMock(side_effect=[tc1, tc2])):
            result = await _generate_cases_per_requirement(
                pkgs, "STP", METADATA, ["REQ-001", "REQ-002"]
            )

        assert len(result) == 2
        assert result[0]["tc_id"] == "TC-001"
        assert result[1]["tc_id"] == "TC-002"

    async def test_produces_one_utr_per_requirement(self):
        pkgs = [_make_ctx("REQ-001", "Not High Process Risk")]
        utr = {**_VALID_UTR, "flags": []}

        with patch("backend.src.services.generation_service.call_llm",
                   new=AsyncMock(return_value=utr)):
            result = await _generate_cases_per_requirement(
                pkgs, "UTR", METADATA, ["REQ-001"]
            )

        assert len(result) == 1
        assert result[0]["utr_id"] == "UTR-001"

    async def test_list_response_flattened_with_sequential_ids(self):
        """When LLM returns a list (multi-AC requirement), each item gets its own sequential ID."""
        pkgs = [_make_ctx("REQ-001")]
        tc_a = {**_VALID_TC, "req_id": "REQ-001", "flags": []}
        tc_b = {**_VALID_TC, "req_id": "REQ-001", "flags": []}

        with patch("backend.src.services.generation_service.call_llm",
                   new=AsyncMock(return_value=[tc_a, tc_b])):
            result = await _generate_cases_per_requirement(
                pkgs, "STP", METADATA, ["REQ-001"]
            )

        assert len(result) == 2
        assert result[0]["tc_id"] == "TC-001"
        assert result[1]["tc_id"] == "TC-002"

    async def test_counter_continues_across_requirements(self):
        pkgs = [_make_ctx(f"REQ-00{i}") for i in range(1, 4)]
        tcs = [{**_VALID_TC, "req_id": f"REQ-00{i}", "flags": []} for i in range(1, 4)]

        with patch("backend.src.services.generation_service.call_llm",
                   new=AsyncMock(side_effect=tcs)):
            result = await _generate_cases_per_requirement(
                pkgs, "STP", METADATA, ["REQ-001", "REQ-002", "REQ-003"]
            )

        ids = [r["tc_id"] for r in result]
        assert ids == ["TC-001", "TC-002", "TC-003"]

    async def test_llm_failure_adds_placeholder_and_continues(self):
        """A failed LLM call adds a VALIDATION_FAILED placeholder and processing continues."""
        pkgs = [_make_ctx("REQ-001"), _make_ctx("REQ-002")]
        tc2 = {**_VALID_TC, "req_id": "REQ-002", "flags": []}

        with patch("backend.src.services.generation_service.call_llm",
                   new=AsyncMock(side_effect=[
                       HTTPException(status_code=500, detail="LLM error"),
                       tc2,
                   ])):
            result = await _generate_cases_per_requirement(
                pkgs, "STP", METADATA, ["REQ-001", "REQ-002"]
            )

        assert len(result) == 2
        assert result[0]["tc_id"] == "TC-001"
        assert "LLM_CALL_FAILED" in result[0]["flags"]
        assert result[1]["tc_id"] == "TC-002"
        assert "LLM_CALL_FAILED" not in result[1].get("flags", [])

    async def test_stp_ids_use_tc_prefix(self):
        pkgs = [_make_ctx("REQ-001")]
        tc = {**_VALID_TC, "flags": []}

        with patch("backend.src.services.generation_service.call_llm",
                   new=AsyncMock(return_value=tc)):
            result = await _generate_cases_per_requirement(pkgs, "STP", METADATA, ["REQ-001"])

        assert result[0]["tc_id"].startswith("TC-")

    async def test_utr_ids_use_utr_prefix(self):
        pkgs = [_make_ctx("REQ-001", "Not High Process Risk")]
        utr = {**_VALID_UTR, "flags": []}

        with patch("backend.src.services.generation_service.call_llm",
                   new=AsyncMock(return_value=utr)):
            result = await _generate_cases_per_requirement(pkgs, "UTR", METADATA, ["REQ-001"])

        assert result[0]["utr_id"].startswith("UTR-")

    async def test_non_dict_items_in_list_are_skipped(self):
        """If LLM returns a list with a non-dict item, skip it gracefully."""
        pkgs = [_make_ctx("REQ-001")]
        tc = {**_VALID_TC, "req_id": "REQ-001", "flags": []}

        with patch("backend.src.services.generation_service.call_llm",
                   new=AsyncMock(return_value=["not a dict", tc])):
            result = await _generate_cases_per_requirement(pkgs, "STP", METADATA, ["REQ-001"])

        assert len(result) == 1
        assert result[0]["tc_id"] == "TC-001"
