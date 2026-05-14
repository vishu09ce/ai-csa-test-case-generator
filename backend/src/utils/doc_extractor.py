import re
from dataclasses import dataclass, field


@dataclass
class ExtractedRequirement:
    req_id: str
    summary: str
    source: str


@dataclass
class ExtractedContent:
    system_description: str = ""
    features: list[str] = field(default_factory=list)
    requirements: list[ExtractedRequirement] = field(default_factory=list)
    urs_text: str = ""
    frs_text: str = ""
    brd_text: str = ""


def _extract_requirements_from_text(text: str, source_label: str) -> list[ExtractedRequirement]:
    requirements = []
    # Match lines that look like requirement IDs: e.g. REQ-001, URS-01, FR-001
    pattern = re.compile(r'\b([A-Z]{1,5}-\d{1,4})\b[:\s\-–—]+(.+)')
    for match in pattern.finditer(text):
        req_id = match.group(1).strip()
        summary = match.group(2).strip()[:300]
        requirements.append(ExtractedRequirement(req_id=req_id, summary=summary, source=source_label))
    return requirements


def extract_content(
    urs_text: str,
    frs_text: str,
    brd_text: str = ""
) -> ExtractedContent:
    content = ExtractedContent(
        urs_text=urs_text,
        frs_text=frs_text,
        brd_text=brd_text,
    )

    # Use FRS as the primary source for system description and features
    frs_lines = [line.strip() for line in frs_text.splitlines() if line.strip()]
    content.system_description = frs_lines[0] if frs_lines else ""
    content.features = [line for line in frs_lines[1:21] if len(line) > 20]

    content.requirements += _extract_requirements_from_text(urs_text, "URS")
    content.requirements += _extract_requirements_from_text(frs_text, "FRS")
    if brd_text:
        content.requirements += _extract_requirements_from_text(brd_text, "BRD")

    return content
