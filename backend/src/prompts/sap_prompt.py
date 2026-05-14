from backend.src.utils.doc_extractor import ExtractedContent


def build_sap_prompt(content: ExtractedContent, system_type: str, project_id: str) -> str:
    features_list = "\n".join(f"- {f}" for f in content.features[:15])
    return f"""You are an FDA CSA validation expert generating a Software Assurance Plan (SAP) for a Life Sciences {system_type} system.

Project ID: {project_id}
System Type: {system_type}

Source document content:
--- URS ---
{content.urs_text[:3000]}

--- FRS ---
{content.frs_text[:3000]}

{"--- BRD ---" + chr(10) + content.brd_text[:2000] if content.brd_text else ""}

Identified features:
{features_list}

Generate the following as structured JSON:
{{
  "system_description": "A clear description of the system based on the URS and FRS",
  "gamp5_category": "3, 4, or 5",
  "gamp5_rationale": "Rationale for the GAMP 5 category",
  "part11_applicable": true or false,
  "part11_rationale": "Rationale for Part 11 applicability",
  "intended_uses": [
    {{
      "id": "IU-001",
      "feature": "Feature name",
      "statement": "The system shall... in order to...",
      "urs_ref": "URS reference ID or N/A",
      "frs_ref": "FRS reference ID or N/A",
      "brd_ref": "BRD reference ID or blank",
      "prod_or_qs": "Production or Quality System",
      "risk_tier": "High or Not High"
    }}
  ],
  "assurance_strategy": "Overall assurance strategy narrative",
  "scripted_approach": "Scripted testing approach for high risk features",
  "unscripted_approach": "Unscripted testing approach for not-high risk features"
}}

Return ONLY valid JSON. No explanation, no markdown.
"""
