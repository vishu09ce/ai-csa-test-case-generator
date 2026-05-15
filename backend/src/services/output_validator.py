"""
Output Validation Service — Sprint 1 Phase 3

Applies 12 quality rules to every generated test case before writing to the Word template.
Failed rules trigger a targeted correction call. Maximum two attempts per test case.
If still failing after two attempts, writes with AI Confidence Low and VALIDATION_FAILED flag.

Rule application:
- VR-001 to VR-010, VR-012: auto-corrected via targeted correction call
- VR-011 (risk classification mismatch): NEVER auto-corrected — flagged for HITL only
- VR-012 (invalid JSON): triggers full regeneration instruction

Gap 13 decision: validation runs first; confidence is assessed on the corrected final version.
Gap 14 decision: one correction attempt = one call addressing all failed rules simultaneously.
"""

import json
import re
from dataclasses import dataclass

from fastapi import HTTPException
from backend.src.services.llm_client import call_llm

MAX_CORRECTION_ATTEMPTS = 2

VAGUE_WORDS = frozenset([
    "correctly", "as expected", "properly", "appropriately",
    "user-friendly", "fast", "high quality", "seamlessly", "smoothly",
])

CONDITIONAL_PATTERNS = re.compile(
    r'\b(if the system|if present|when available|if applicable|if needed)\b',
    re.IGNORECASE,
)

PASSIVE_VOICE_PATTERN = re.compile(
    r'\b(is|are|was|were|be|been|being)\s+\w+ed\b',
    re.IGNORECASE,
)


@dataclass
class _RuleResult:
    rule_id: str
    passed: bool
    detail: str = ""


# ---------------------------------------------------------------------------
# Individual rule checks
# ---------------------------------------------------------------------------

def _vr001(tc: dict, doc_type: str) -> _RuleResult:
    id_field = "tc_id" if doc_type == "STP" else "utr_id"
    value = tc.get(id_field, "")
    passed = bool(value and re.match(r'^(TC|UTR)-\d+', str(value)))
    return _RuleResult("VR-001", passed,
                       "" if passed else f"{id_field} is missing or malformed: '{value}'")


def _vr002(tc: dict, valid_req_ids: list[str]) -> _RuleResult:
    req_id = tc.get("req_id", "")
    passed = bool(req_id) and (not valid_req_ids or req_id in valid_req_ids)
    return _RuleResult("VR-002", passed,
                       "" if passed else f"req_id '{req_id}' not found in requirement list")


def _vr003(tc: dict, doc_type: str) -> _RuleResult:
    if doc_type != "STP":
        return _RuleResult("VR-003", True)
    preconditions = tc.get("preconditions", [])
    passed = isinstance(preconditions, list) and len(preconditions) >= 1 and any(p.strip() for p in preconditions)
    return _RuleResult("VR-003", passed,
                       "" if passed else "preconditions field is empty or missing")


def _vr004(tc: dict, doc_type: str) -> _RuleResult:
    if doc_type != "STP":
        return _RuleResult("VR-004", True)
    steps = tc.get("test_steps", [])
    passed = isinstance(steps, list) and len(steps) >= 2
    return _RuleResult("VR-004", passed,
                       "" if passed else f"test_steps has {len(steps) if isinstance(steps, list) else 0} step(s) — minimum 2 required")


def _vr005(tc: dict, doc_type: str) -> _RuleResult:
    if doc_type != "STP":
        return _RuleResult("VR-005", True)
    steps = tc.get("test_steps", [])
    offenders = [s for s in steps if isinstance(s, str) and CONDITIONAL_PATTERNS.search(s)]
    passed = len(offenders) == 0
    return _RuleResult("VR-005", passed,
                       "" if passed else f"conditional language in step(s): {offenders[:2]}")


def _vr006(tc: dict, doc_type: str) -> _RuleResult:
    if doc_type != "STP":
        return _RuleResult("VR-006", True)
    steps = tc.get("test_steps", [])
    offenders = [s for s in steps if isinstance(s, str) and PASSIVE_VOICE_PATTERN.search(s)]
    passed = len(offenders) == 0
    return _RuleResult("VR-006", passed,
                       "" if passed else f"passive voice in step(s): {offenders[:2]}")


def _vr007(tc: dict) -> _RuleResult:
    result = str(tc.get("expected_result", "")).lower()
    found = [w for w in VAGUE_WORDS if w in result]
    passed = len(found) == 0
    return _RuleResult("VR-007", passed,
                       "" if passed else f"vague language in expected_result: {found}")


def _vr008(tc: dict) -> _RuleResult:
    result = str(tc.get("expected_result", ""))
    # Expected result must be non-empty and describe specific observable behavior
    passed = (
        len(result.strip()) >= 20 and
        not result.strip().lower().startswith(("the test", "verify that", "check that"))
    )
    return _RuleResult("VR-008", passed,
                       "" if passed else "expected_result does not describe specific observable system behavior")


def _vr009(tc: dict) -> _RuleResult:
    confidence = tc.get("confidence", "")
    passed = confidence in ("High", "Medium", "Low")
    return _RuleResult("VR-009", passed,
                       "" if passed else f"confidence field invalid or missing: '{confidence}'")


def _vr010(tc: dict) -> _RuleResult:
    flags = tc.get("flags")
    passed = isinstance(flags, list)
    return _RuleResult("VR-010", passed,
                       "" if passed else "flags field is missing or not an array")


def _vr011(tc: dict, pra_risk_class: str) -> _RuleResult:
    """VR-011: risk classification mismatch — NEVER auto-corrected, HITL flag only."""
    tc_risk = tc.get("risk_class", "")
    if not pra_risk_class or not tc_risk:
        return _RuleResult("VR-011", True)
    passed = tc_risk.lower().strip() == pra_risk_class.lower().strip()
    return _RuleResult("VR-011", passed,
                       "" if passed else f"risk_class '{tc_risk}' does not match PRA: '{pra_risk_class}'")


def _vr012(raw_output: str) -> _RuleResult:
    try:
        json.loads(raw_output)
        return _RuleResult("VR-012", True)
    except (json.JSONDecodeError, TypeError) as e:
        return _RuleResult("VR-012", False, f"Invalid JSON: {e}")


# ---------------------------------------------------------------------------
# Correction instruction builder (Appendix A.4 verbatim)
# ---------------------------------------------------------------------------

_CORRECTION_TEMPLATES = {
    "VR-001": (
        "The tc_id / utr_id field is missing or does not match the expected format. "
        "Populate the ID field correctly. Do not change any other field."
    ),
    "VR-002": (
        "The req_id field does not match any requirement in the input. "
        "Correct the req_id to match the target requirement ID. Do not change any other field."
    ),
    "VR-003": (
        "The preconditions field is empty. Generate at least one specific, verifiable precondition "
        "describing the required system state before this test can be executed. "
        "Do not change any other field."
    ),
    "VR-004": (
        "The test_steps field contains fewer than two steps. Expand the test steps to cover the "
        "full test action sequence derived from the FRS specification. Do not change any other field."
    ),
    "VR-005": (
        "One or more test steps contain conditional language: 'if the system', 'when available', "
        "'if present'. Rewrite each affected step as a direct action without conditions. "
        "Do not change any other step."
    ),
    "VR-006": (
        "One or more test steps use passive voice. Rewrite each affected step using active "
        "imperative voice starting with a verb. Do not change any other step."
    ),
    "VR-007": (
        "The expected_result contains vague language. Rewrite to describe specific observable "
        "system behavior without vague terms. Do not change any other field."
    ),
    "VR-008": (
        "The expected_result does not describe specific observable system behavior. Rewrite to "
        "state what the system specifically displays, generates, prevents, or updates — specific "
        "enough that a tester can determine Pass or Fail without judgment. "
        "Do not change any other field."
    ),
    "VR-009": (
        "The confidence field is missing or contains an invalid value. Assess the grounding "
        "quality of this test case and set confidence to High, Medium, or Low. "
        "Do not change any other field."
    ),
    "VR-010": (
        "The flags field is missing. Add a flags field. "
        "If no flags apply, set to an empty array []. Do not change any other field."
    ),
    "VR-012": (
        "Your previous response was not valid JSON. Respond only with valid JSON matching the "
        "required schema. No text before or after the JSON. No markdown code blocks."
    ),
}


def _build_correction_prompt(original_json: str, failed: list[_RuleResult]) -> str:
    # VR-011 is never auto-corrected — exclude it
    correctable = [r for r in failed if r.rule_id != "VR-011"]
    if not correctable:
        return ""

    instructions = "\n".join(
        f"- {r.rule_id}: {_CORRECTION_TEMPLATES.get(r.rule_id, r.detail)}"
        for r in correctable
    )
    return (
        f"The following quality rules failed for the test case below.\n"
        f"Apply ALL corrections in a single response.\n\n"
        f"FAILED RULES:\n{instructions}\n\n"
        f"ORIGINAL TEST CASE:\n{original_json}\n\n"
        f"Return ONLY the corrected JSON. No text before or after."
    )


def _apply_vr011_flag(tc: dict, pra_risk_class: str) -> dict:
    """Add HITL flag for risk classification mismatch without auto-correcting."""
    result = _vr011(tc, pra_risk_class)
    if not result.passed:
        flags = list(tc.get("flags", []))
        if isinstance(flags, list):
            hitl_flag = f"HITL_REVIEW: risk_class mismatch — TC says '{tc.get('risk_class')}', PRA says '{pra_risk_class}'"
            if hitl_flag not in flags:
                flags.append(hitl_flag)
            tc["flags"] = flags
    return tc


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate_test_case(
    tc: dict,
    doc_type: str,
    valid_req_ids: list[str],
    pra_risk_class: str,
) -> list[_RuleResult]:
    """Run all 12 rules. Returns list of failed results (VR-011 included for flagging)."""
    results = [
        _vr001(tc, doc_type),
        _vr002(tc, valid_req_ids),
        _vr003(tc, doc_type),
        _vr004(tc, doc_type),
        _vr005(tc, doc_type),
        _vr006(tc, doc_type),
        _vr007(tc) if doc_type == "STP" else _RuleResult("VR-007", True),
        _vr008(tc) if doc_type == "STP" else _RuleResult("VR-008", True),
        _vr009(tc),
        _vr010(tc),
        _vr011(tc, pra_risk_class),
    ]
    return [r for r in results if not r.passed]


async def validate_and_correct(
    tc: dict,
    doc_type: str,
    valid_req_ids: list[str],
    pra_risk_class: str,
    system_prompt: str,
) -> dict:
    """
    Validate → correct loop. Max two attempts (Gap 14 decision).
    Returns the final test case dict with confidence and flags set.
    """
    for attempt in range(MAX_CORRECTION_ATTEMPTS):
        failed = validate_test_case(tc, doc_type, valid_req_ids, pra_risk_class)
        correctable = [r for r in failed if r.rule_id != "VR-011"]

        if not correctable:
            break  # all correctable rules pass

        correction_prompt = _build_correction_prompt(json.dumps(tc), correctable)
        try:
            result = await call_llm(correction_prompt, system_prompt)
            if isinstance(result, list):
                result = result[0]
            if isinstance(result, dict):
                tc = result
        except HTTPException:
            break  # correction call failed — proceed with what we have

    # Final check: if correctable rules still fail, apply VALIDATION_FAILED
    final_failed = validate_test_case(tc, doc_type, valid_req_ids, pra_risk_class)
    correctable_remaining = [r for r in final_failed if r.rule_id != "VR-011"]

    if correctable_remaining:
        tc["confidence"] = "Low"
        flags = list(tc.get("flags", []))
        if not isinstance(flags, list):
            flags = []
        if "VALIDATION_FAILED" not in flags:
            flags.append("VALIDATION_FAILED")
        tc["flags"] = flags

    # VR-011: always apply HITL flag if risk class mismatches — never auto-correct
    tc = _apply_vr011_flag(tc, pra_risk_class)

    return tc


def validate_and_correct_batch(
    test_cases: list[dict] | dict,
    doc_type: str,
    valid_req_ids: list[str],
    pra_risk_class: str,
    system_prompt: str,
) -> list:
    """Wraps validate_and_correct for both single-dict and array LLM outputs."""
    import asyncio
    items = test_cases if isinstance(test_cases, list) else [test_cases]
    return [
        asyncio.get_event_loop().run_until_complete(
            validate_and_correct(tc, doc_type, valid_req_ids, pra_risk_class, system_prompt)
        )
        for tc in items
    ]
