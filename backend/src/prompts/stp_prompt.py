def build_stp_prompt(high_risk_requirements: list[dict], frs_text: str, project_id: str) -> str:
    req_list = "\n".join(
        f"- {r['req_id']}: {r['summary']}"
        for r in high_risk_requirements
    )
    return f"""You are an FDA CSA validation expert generating a Scripted Test Protocol (STP).

Project ID: {project_id}

High Process Risk requirements to test:
{req_list}

FRS content for test steps and expected results:
{frs_text[:4000]}

Generate one scripted test case per requirement as structured JSON:
{{
  "test_cases": [
    {{
      "tc_id": "TC-001",
      "req_id": "REQ-001",
      "preconditions": "AI-generated preconditions from FRS business rules",
      "test_steps": "Step-by-step actions derived from FRS specification",
      "expected_result": "Expected outcome derived from FRS acceptance criteria",
      "actual_result": "",
      "pass_fail": ""
    }}
  ]
}}

Return ONLY valid JSON. No explanation, no markdown.
"""
