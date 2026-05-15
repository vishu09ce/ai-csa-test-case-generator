import pytest
from unittest.mock import AsyncMock, patch
from backend.src.services.output_validator import (
    validate_test_case, validate_and_correct,
    _vr001, _vr002, _vr003, _vr004, _vr005, _vr006,
    _vr007, _vr008, _vr009, _vr010, _vr011,
    _apply_vr011_flag, _build_correction_prompt,
)

VALID_STP = {
    "tc_id": "TC-001",
    "req_id": "REQ-001",
    "iu_ref": "IU-001",
    "risk_class": "High Process Risk",
    "preconditions": ["User is logged in with Admin role"],
    "test_steps": ["Navigate to the login page", "Enter valid credentials", "Click Login"],
    "expected_result": "System displays the dashboard and records login event in audit log.",
    "actual_result": "",
    "pass_fail": "",
    "confidence": "High",
    "flags": [],
}

VALID_UTR = {
    "utr_id": "UTR-001",
    "req_id": "REQ-002",
    "iu_ref": "IU-002",
    "risk_class": "Not High Process Risk",
    "feature_description": "Dashboard summary view.",
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

REQ_IDS = ["REQ-001", "REQ-002", "REQ-003"]


class TestVR001:
    def test_passes_valid_tc_id(self):
        assert _vr001(VALID_STP, "STP").passed

    def test_passes_valid_utr_id(self):
        assert _vr001(VALID_UTR, "UTR").passed

    def test_fails_missing_id(self):
        assert not _vr001({}, "STP").passed

    def test_fails_malformed_id(self):
        assert not _vr001({"tc_id": "TEST001"}, "STP").passed


class TestVR002:
    def test_passes_when_req_id_in_list(self):
        assert _vr002(VALID_STP, REQ_IDS).passed

    def test_passes_when_no_list_provided(self):
        assert _vr002(VALID_STP, []).passed

    def test_fails_unknown_req_id(self):
        assert not _vr002({"req_id": "REQ-999"}, REQ_IDS).passed


class TestVR003:
    def test_passes_for_utr(self):
        assert _vr003(VALID_UTR, "UTR").passed

    def test_passes_with_preconditions(self):
        assert _vr003(VALID_STP, "STP").passed

    def test_fails_empty_preconditions(self):
        tc = {**VALID_STP, "preconditions": []}
        assert not _vr003(tc, "STP").passed

    def test_fails_missing_preconditions(self):
        tc = {k: v for k, v in VALID_STP.items() if k != "preconditions"}
        assert not _vr003(tc, "STP").passed


class TestVR004:
    def test_passes_for_utr(self):
        assert _vr004(VALID_UTR, "UTR").passed

    def test_passes_with_enough_steps(self):
        assert _vr004(VALID_STP, "STP").passed

    def test_fails_one_step(self):
        tc = {**VALID_STP, "test_steps": ["Only one step"]}
        assert not _vr004(tc, "STP").passed


class TestVR005:
    def test_passes_clean_steps(self):
        assert _vr005(VALID_STP, "STP").passed

    def test_fails_conditional_language(self):
        tc = {**VALID_STP, "test_steps": ["Click Login", "If the system displays error, retry"]}
        assert not _vr005(tc, "STP").passed

    def test_passes_for_utr(self):
        assert _vr005(VALID_UTR, "UTR").passed


class TestVR006:
    def test_passes_active_voice(self):
        assert _vr006(VALID_STP, "STP").passed

    def test_fails_passive_voice(self):
        tc = {**VALID_STP, "test_steps": ["Navigate to login", "The form is submitted by the user"]}
        assert not _vr006(tc, "STP").passed

    def test_passes_for_utr(self):
        assert _vr006(VALID_UTR, "UTR").passed


class TestVR007:
    def test_passes_specific_result(self):
        assert _vr007(VALID_STP).passed

    def test_fails_vague_correctly(self):
        tc = {**VALID_STP, "expected_result": "System works correctly."}
        assert not _vr007(tc).passed

    def test_fails_vague_as_expected(self):
        tc = {**VALID_STP, "expected_result": "System behaves as expected."}
        assert not _vr007(tc).passed

    def test_fails_vague_properly(self):
        tc = {**VALID_STP, "expected_result": "Login completes properly."}
        assert not _vr007(tc).passed


class TestVR008:
    def test_passes_observable_behavior(self):
        assert _vr008(VALID_STP).passed

    def test_fails_empty_result(self):
        tc = {**VALID_STP, "expected_result": ""}
        assert not _vr008(tc).passed

    def test_fails_too_short(self):
        tc = {**VALID_STP, "expected_result": "OK"}
        assert not _vr008(tc).passed


class TestVR009:
    def test_passes_high_confidence(self):
        assert _vr009(VALID_STP).passed

    def test_passes_medium_confidence(self):
        assert _vr009({**VALID_STP, "confidence": "Medium"}).passed

    def test_fails_missing_confidence(self):
        tc = {k: v for k, v in VALID_STP.items() if k != "confidence"}
        assert not _vr009(tc).passed

    def test_fails_invalid_value(self):
        assert not _vr009({**VALID_STP, "confidence": "Very High"}).passed


class TestVR010:
    def test_passes_empty_flags_array(self):
        assert _vr010(VALID_STP).passed

    def test_fails_missing_flags(self):
        tc = {k: v for k, v in VALID_STP.items() if k != "flags"}
        assert not _vr010(tc).passed

    def test_fails_flags_not_array(self):
        assert not _vr010({**VALID_STP, "flags": "none"}).passed


class TestVR011:
    def test_passes_matching_risk_class(self):
        result = _vr011(VALID_STP, "High Process Risk")
        assert result.passed

    def test_fails_mismatched_risk_class(self):
        result = _vr011(VALID_STP, "Not High Process Risk")
        assert not result.passed

    def test_passes_when_no_pra_class(self):
        assert _vr011(VALID_STP, "").passed

    def test_vr011_flag_added_on_mismatch(self):
        tc = {**VALID_STP, "flags": []}
        result = _apply_vr011_flag(tc, "Not High Process Risk")
        assert any("HITL_REVIEW" in f for f in result["flags"])

    def test_vr011_not_in_correctable_rules(self):
        tc = {**VALID_STP, "risk_class": "Not High Process Risk"}
        correction = _build_correction_prompt("{}", [_vr011(tc, "High Process Risk")])
        assert correction == ""


class TestValidateTestCase:
    def test_valid_stp_passes_all(self):
        failed = validate_test_case(VALID_STP, "STP", REQ_IDS, "High Process Risk")
        assert failed == []

    def test_valid_utr_passes_all(self):
        failed = validate_test_case(VALID_UTR, "UTR", REQ_IDS, "Not High Process Risk")
        assert failed == []

    def test_returns_multiple_failures(self):
        tc = {**VALID_STP, "expected_result": "works correctly", "preconditions": []}
        failed = validate_test_case(tc, "STP", REQ_IDS, "High Process Risk")
        rule_ids = [r.rule_id for r in failed]
        assert "VR-007" in rule_ids
        assert "VR-003" in rule_ids


@pytest.mark.asyncio
class TestValidateAndCorrect:
    async def test_passes_through_valid_tc(self):
        result = await validate_and_correct(
            VALID_STP.copy(), "STP", REQ_IDS, "High Process Risk", "system prompt"
        )
        assert result["confidence"] == "High"
        assert "VALIDATION_FAILED" not in result.get("flags", [])

    async def test_applies_validation_failed_after_two_failed_attempts(self):
        bad_tc = {
            **VALID_STP,
            "expected_result": "works correctly",  # VR-007 fail
            "preconditions": [],                   # VR-003 fail
        }
        # Mock LLM to always return the same bad TC (never fixes it)
        with patch(
            "backend.src.services.output_validator.call_llm",
            new=AsyncMock(return_value=bad_tc)
        ):
            result = await validate_and_correct(
                bad_tc.copy(), "STP", REQ_IDS, "High Process Risk", "system"
            )
        assert result["confidence"] == "Low"
        assert "VALIDATION_FAILED" in result["flags"]

    async def test_correction_accepted_when_llm_fixes_issue(self):
        bad_tc = {**VALID_STP, "expected_result": "works correctly"}
        fixed_tc = {**VALID_STP, "expected_result": "System displays the dashboard with all records loaded."}
        with patch(
            "backend.src.services.output_validator.call_llm",
            new=AsyncMock(return_value=fixed_tc)
        ):
            result = await validate_and_correct(
                bad_tc.copy(), "STP", REQ_IDS, "High Process Risk", "system"
            )
        assert "VALIDATION_FAILED" not in result.get("flags", [])

    async def test_vr011_flag_added_without_blocking(self):
        tc = {**VALID_STP, "risk_class": "Not High Process Risk"}
        result = await validate_and_correct(
            tc.copy(), "STP", REQ_IDS, "High Process Risk", "system"
        )
        assert any("HITL_REVIEW" in f for f in result.get("flags", []))
        assert "VALIDATION_FAILED" not in result.get("flags", [])
