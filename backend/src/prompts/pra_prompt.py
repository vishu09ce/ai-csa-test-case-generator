def build_pra_prompt(intended_uses: list[dict], system_type: str, project_id: str) -> str:
    iu_list = "\n".join(
        f"- {iu['id']}: {iu['feature']} — {iu['statement']} (Preliminary risk: {iu['risk_tier']})"
        for iu in intended_uses
    )
    return f"""You are an FDA CSA validation expert generating a Process Risk Assessment (PRA) for a Life Sciences {system_type} system.

Project ID: {project_id}
System Type: {system_type}

Approved intended use statements from the SAP:
{iu_list}

For each intended use, generate a risk classification row as structured JSON:
{{
  "risk_classifications": [
    {{
      "id": "IU-001",
      "feature": "Feature name",
      "failure_scenario": "A realistic foreseeable failure scenario",
      "patient_safety_impact": true or false,
      "product_quality_impact": true or false,
      "risk_classification": "High Process Risk or Not High Process Risk",
      "rationale": "Clear rationale linking failure scenario to patient safety or product quality"
    }}
  ],
  "total_features": 0,
  "high_risk_count": 0,
  "not_high_risk_count": 0
}}

Classification rules:
- High Process Risk: failure could foreseeably compromise patient safety OR product quality
- Not High Process Risk: failure would not foreseeably compromise patient safety or product quality

Return ONLY valid JSON. No explanation, no markdown.
"""
