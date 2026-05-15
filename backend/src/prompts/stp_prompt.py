from backend.src.prompts.requirement_context import RequirementContext, ProjectMetadata
from backend.src.prompts.system_prompt import build_system_prompt
from backend.src.prompts.few_shot_examples import FEW_SHOT_EXAMPLES

_STP_SCHEMA = """\
Required JSON schema for a single scripted test case:
{
  "tc_id": "TC-XXX",
  "req_id": "REQ-XXX",
  "iu_ref": "IU-XXX",
  "risk_class": "High Process Risk",
  "preconditions": ["<verifiable system state>"],
  "test_steps": ["<active imperative action>"],
  "expected_result": "<specific observable system behavior>",
  "actual_result": "",
  "pass_fail": "",
  "confidence": "High | Medium | Low",
  "flags": []
}

If multiple distinct acceptance criteria exist, return a JSON array — one object per AC.
Leave actual_result and pass_fail as empty strings."""


def build_stp_prompt(high_risk_requirements: list[dict], frs_text: str, project_id: str) -> str:
    """Legacy document-level prompt — kept for compatibility until Phase 4 replaces generation_service."""
    req_list = "\n".join(f"- {r['req_id']}: {r['summary']}" for r in high_risk_requirements)
    return (
        f"You are an FDA CSA validation expert generating a Scripted Test Protocol.\n"
        f"Project ID: {project_id}\nHigh Process Risk requirements:\n{req_list}\n"
        f"FRS content:\n{frs_text[:4000]}\n"
        f'Generate JSON: {{"test_cases":[{{"tc_id":"TC-001","req_id":"REQ-001",'
        f'"preconditions":"...","test_steps":"...","expected_result":"...","actual_result":"","pass_fail":""}}]}}\n'
        f"Return ONLY valid JSON."
    )


def build_stp_system_prompt(metadata: ProjectMetadata) -> str:
    return build_system_prompt(metadata, "STP")


def build_stp_user_prompt(ctx: RequirementContext) -> str:
    adjacent_lines = []
    for i, text in enumerate(reversed(ctx.adjacent_prev), 1):
        adjacent_lines.insert(0, f"[preceding -{i}]: {text}")
    for i, text in enumerate(ctx.adjacent_next, 1):
        adjacent_lines.append(f"[following +{i}]: {text}")

    frs_label = f"{ctx.frs_link_type} link"
    ac_label = f"from {ctx.ac_source}" if ctx.ac_source != "missing" else "not found in source documents"

    user_prompt = f"""\
{FEW_SHOT_EXAMPLES}

--- TARGET REQUIREMENT ---

DOCUMENT STRUCTURE CONTEXT:
{ctx.section_heading or 'Not available'}

ADJACENT REQUIREMENTS:
{chr(10).join(adjacent_lines) if adjacent_lines else 'Not available'}

TARGET REQUIREMENT:
{ctx.req_id}: {ctx.requirement_text}
Source Document: {ctx.source_document}

FRS SPECIFICATION ({frs_label}):
{ctx.frs_specification or 'No FRS specification found.'}

ACCEPTANCE CRITERIA ({ac_label}):
{ctx.acceptance_criteria or 'No acceptance criteria found in source documents.'}

INTENDED USE STATEMENT (from approved SAP, {ctx.iu_ref or 'ref not available'}):
{ctx.intended_use_statement or 'Not available.'}

RISK CLASSIFICATION (from approved PRA):
{ctx.risk_classification}
Rationale: {ctx.risk_rationale or 'Not provided.'}

{_STP_SCHEMA}

GENERATE: One scripted test case per distinct acceptance criterion for this requirement.
"""
    return user_prompt
