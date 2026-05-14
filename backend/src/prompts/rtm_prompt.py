from backend.src.utils.doc_extractor import ExtractedContent


def build_rtm_prompt(content: ExtractedContent, risk_classifications: list[dict], project_id: str) -> str:
    risk_map = "\n".join(
        f"- {r['id']}: {r['feature']} → {r['risk_classification']}"
        for r in risk_classifications
    )
    return f"""You are an FDA CSA validation expert generating a Requirements Traceability Matrix (RTM).

Project ID: {project_id}

Risk classifications from approved PRA:
{risk_map}

URS content:
{content.urs_text[:3000]}

FRS content:
{content.frs_text[:3000]}

{"BRD content:" + chr(10) + content.brd_text[:2000] if content.brd_text else ""}

Extract every requirement and generate the RTM as structured JSON:
{{
  "requirements": [
    {{
      "req_id": "REQ-001",
      "summary": "Requirement summary",
      "urs_ref": "URS reference or N/A",
      "frs_ref": "FRS reference or N/A",
      "brd_ref": "BRD reference or blank",
      "iu_ref": "IU-00X",
      "risk_classification": "High Process Risk or Not High Process Risk",
      "test_case_id": "",
      "result": ""
    }}
  ]
}}

Return ONLY valid JSON. No explanation, no markdown.
"""
