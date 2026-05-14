def build_utr_prompt(not_high_risk_requirements: list[dict], frs_text: str, project_id: str) -> str:
    req_list = "\n".join(
        f"- {r['req_id']}: {r['summary']}"
        for r in not_high_risk_requirements
    )
    return f"""You are an FDA CSA validation expert generating an Unscripted Test Record (UTR).

Project ID: {project_id}

Not High Process Risk requirements to cover:
{req_list}

FRS content for feature descriptions:
{frs_text[:4000]}

Generate one unscripted test record row per requirement as structured JSON:
{{
  "test_records": [
    {{
      "utr_id": "UTR-001",
      "req_id": "REQ-001",
      "feature": "AI-extracted feature description from FRS",
      "exploratory_scenarios": "Suggested scenarios: normal use, boundary conditions, error states",
      "tester_observations": "",
      "conclusion": ""
    }}
  ]
}}

Return ONLY valid JSON. No explanation, no markdown.
"""
