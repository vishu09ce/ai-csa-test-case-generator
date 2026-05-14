def build_asr_prompt(
    intended_uses: list[dict],
    risk_classifications: list[dict],
    test_cases: list[dict],
    test_records: list[dict],
    project_id: str
) -> str:
    iu_summary = "\n".join(
        f"- {iu['id']}: {iu['feature']} ({iu['risk_tier']})"
        for iu in intended_uses
    )
    return f"""You are an FDA CSA validation expert generating an Assurance Summary Report (ASR).

Project ID: {project_id}

Intended uses from approved SAP:
{iu_summary}

Total scripted test cases: {len(test_cases)}
Total unscripted test records: {len(test_records)}

Generate the ASR conclusion section as structured JSON:
{{
  "overall_conclusion": "A narrative conclusion stating whether all intended uses were addressed, all assurance activities completed, all deviations resolved, and whether the system is fit for its intended use.",
  "coverage_summary": [
    {{
      "iu_id": "IU-001",
      "feature": "Feature name",
      "risk_class": "High Process Risk or Not High Process Risk",
      "test_doc": "STP or UTR",
      "result": "Pass or Fit",
      "conclusion": "Fit for intended use"
    }}
  ],
  "all_intended_uses_addressed": true,
  "all_risk_classifications_confirmed": true,
  "system_fitness": "Fit"
}}

Return ONLY valid JSON. No explanation, no markdown.
"""
