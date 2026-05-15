from backend.src.prompts.requirement_context import RequirementContext, ProjectMetadata
from backend.src.prompts.system_prompt import build_system_prompt
from backend.src.prompts.few_shot_examples import FEW_SHOT_EXAMPLES

_UTR_SCHEMA = """\
Required JSON schema for a single unscripted test record:
{
  "utr_id": "UTR-XXX",
  "req_id": "REQ-XXX",
  "iu_ref": "IU-XXX",
  "risk_class": "Not High Process Risk",
  "feature_description": "<concise feature description from FRS>",
  "exploratory_scenarios": [
    "<Normal use scenario>",
    "<Boundary condition scenario>",
    "<Error state scenario>"
  ],
  "tester_observations": "",
  "conclusion": "",
  "confidence": "High | Medium | Low",
  "flags": []
}

Leave tester_observations and conclusion as empty strings."""


def build_utr_prompt(not_high_risk_requirements: list[dict], frs_text: str, project_id: str) -> str:
    """Legacy document-level prompt — kept for compatibility until Phase 4 replaces generation_service."""
    req_list = "\n".join(f"- {r['req_id']}: {r['summary']}" for r in not_high_risk_requirements)
    return (
        f"You are an FDA CSA validation expert generating an Unscripted Test Record.\n"
        f"Project ID: {project_id}\nNot High Process Risk requirements:\n{req_list}\n"
        f"FRS content:\n{frs_text[:4000]}\n"
        f'Generate JSON: {{"test_records":[{{"utr_id":"UTR-001","req_id":"REQ-001",'
        f'"feature":"...","exploratory_scenarios":"...","tester_observations":"","conclusion":""}}]}}\n'
        f"Return ONLY valid JSON."
    )


def build_utr_system_prompt(metadata: ProjectMetadata) -> str:
    return build_system_prompt(metadata, "UTR")


def build_utr_user_prompt(ctx: RequirementContext) -> str:
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

{_UTR_SCHEMA}

GENERATE: One exploratory test record row with three scenario suggestions \
(normal use, boundary condition, error state) for this requirement.
"""
    return user_prompt
