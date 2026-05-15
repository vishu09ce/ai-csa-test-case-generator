"""
RAG Service — Sprint 1 Phase 2
Assembles a six-component context package per requirement before each LLM call.

Components (FR-ENH-001):
1. Document structure context — section heading hierarchy
2. Adjacent requirements — two preceding, two following
3. FRS specification — explicit reference first, TF-IDF semantic match fallback (≥ 0.75)
4. Acceptance criteria — FRS first, BRD fallback
5. Intended use statement — from SAP via best-match
6. Risk classification + rationale — from PRA via best-match

Trim priority when token budget exceeded (FR-ENH-007, Gap 7 decision):
BRD → Adjacent reqs → Document structure → Intended use. FRS and AC never dropped.
"""

import re
from dataclasses import dataclass, field

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from backend.src.prompts.requirement_context import RequirementContext, ProjectMetadata

# Gap 6 decision: cosine similarity ≥ 0.75 = INFERRED_FRS_LINK; below = MISSING_FRS_SPEC
SEMANTIC_THRESHOLD = 0.75

# Approximate token budget for the user prompt (8192 total - ~3500 for system + few-shot)
TOKEN_BUDGET = 4500
CHARS_PER_TOKEN = 4  # rough approximation


@dataclass
class _RequirementWithPosition:
    req_id: str
    text: str
    source: str
    section_heading: str
    position: int


@dataclass
class _FrsSection:
    heading: str
    content: str


# ---------------------------------------------------------------------------
# Text utilities
# ---------------------------------------------------------------------------

def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // CHARS_PER_TOKEN)


def _extract_section_headings(text: str) -> list[tuple[int, str]]:
    """Return (char_offset, heading_text) for lines that look like section headings."""
    headings = []
    for match in re.finditer(r'^(\d[\d.]*\s+.{3,80})$', text, re.MULTILINE):
        headings.append((match.start(), match.group(1).strip()))
    return headings


def _heading_at_position(pos: int, headings: list[tuple[int, str]]) -> str:
    current = ""
    for offset, heading in headings:
        if offset <= pos:
            current = heading
        else:
            break
    return current


def _split_frs_into_sections(frs_text: str) -> list[_FrsSection]:
    """Split FRS text into sections using heading detection."""
    headings = _extract_section_headings(frs_text)
    if not headings:
        return [_FrsSection(heading="General", content=frs_text)]

    sections = []
    for i, (offset, heading) in enumerate(headings):
        start = offset
        end = headings[i + 1][0] if i + 1 < len(headings) else len(frs_text)
        content = frs_text[start:end].strip()
        if content:
            sections.append(_FrsSection(heading=heading, content=content))
    return sections


def _extract_requirements_with_positions(text: str, source: str) -> list[_RequirementWithPosition]:
    """Extract requirements with section context and position index."""
    pattern = re.compile(r'\b([A-Z]{1,5}-\d{1,4})\b[:\s\-–—]+(.+)')
    headings = _extract_section_headings(text)
    reqs = []
    for match in pattern.finditer(text):
        req_id = match.group(1).strip()
        req_text = match.group(2).strip()[:400]
        heading = _heading_at_position(match.start(), headings)
        reqs.append(_RequirementWithPosition(
            req_id=req_id,
            text=req_text,
            source=source,
            section_heading=heading,
            position=len(reqs),
        ))
    return reqs


# ---------------------------------------------------------------------------
# Semantic matching
# ---------------------------------------------------------------------------

def _compute_similarities(query: str, candidates: list[str]) -> list[float]:
    """TF-IDF cosine similarity between query and each candidate string."""
    if not candidates:
        return []
    corpus = [query] + candidates
    try:
        vectorizer = TfidfVectorizer(stop_words="english", min_df=1)
        matrix = vectorizer.fit_transform(corpus)
        sims = cosine_similarity(matrix[0:1], matrix[1:]).flatten()
        return sims.tolist()
    except ValueError:
        return [0.0] * len(candidates)


def _find_frs_match(req_text: str, req_id: str, frs_sections: list[_FrsSection]) -> tuple[str, str]:
    """
    Returns (frs_content, link_type).
    link_type: "explicit" | "inferred" | "missing"
    """
    if not frs_sections:
        return "", "missing"

    # Explicit reference: look for the req_id mentioned in any FRS section
    for section in frs_sections:
        if req_id in section.content:
            return section.content, "explicit"

    # Semantic fallback
    candidates = [s.content for s in frs_sections]
    scores = _compute_similarities(req_text, candidates)
    best_idx = int(np.argmax(scores))
    if scores[best_idx] >= SEMANTIC_THRESHOLD:
        return frs_sections[best_idx].content, "inferred"

    return "", "missing"


def _extract_acceptance_criteria(frs_content: str, brd_text: str) -> tuple[str, str]:
    """
    Returns (ac_text, source) where source is "FRS" | "BRD" | "missing".
    Captures the full sentence following an "acceptance criteria" label,
    or sentences containing observable behavior verbs.
    """
    # Match "Acceptance criteria[:]" followed by text up to the next newline or period
    ac_label_pattern = re.compile(
        r'acceptance criteria?\s*[:\-]?\s*(.{10,300}?)(?:\n|$)',
        re.IGNORECASE
    )
    # Match shall-sentences with observable behavior verbs
    shall_pattern = re.compile(
        r'(?:shall[^.]{0,200}(?:display|update|prevent|generate|record|assign|lock|produce)[^.]{0,100}\.)',
        re.IGNORECASE
    )

    def _extract_from(text: str) -> str:
        matches = ac_label_pattern.findall(text)
        if matches:
            return " ".join(m.strip() for m in matches[:3])
        matches = shall_pattern.findall(text)
        if matches:
            return " ".join(matches[:3])
        return ""

    if frs_content:
        result = _extract_from(frs_content)
        if result:
            return result, "FRS"

    if brd_text:
        result = _extract_from(brd_text)
        if result:
            return result, "BRD"

    return "", "missing"


def _find_intended_use(req_text: str, intended_uses: list[str]) -> tuple[str, str]:
    """Return (intended_use_text, iu_ref) best matching the requirement."""
    if not intended_uses:
        return "", ""
    scores = _compute_similarities(req_text, intended_uses)
    best_idx = int(np.argmax(scores))
    iu_ref = f"IU-{best_idx + 1:03d}"
    return intended_uses[best_idx], iu_ref


def _find_risk_classification(req_text: str, risk_classifications: list[dict]) -> tuple[str, str]:
    """Return (risk_classification, rationale) best matching the requirement."""
    if not risk_classifications:
        return "Not High Process Risk", ""
    features = [r.get("feature", "") for r in risk_classifications]
    scores = _compute_similarities(req_text, features)
    best_idx = int(np.argmax(scores))
    entry = risk_classifications[best_idx]
    return (
        entry.get("risk_classification", "Not High Process Risk"),
        entry.get("rationale", entry.get("risk_rationale", "")),
    )


# ---------------------------------------------------------------------------
# Token budget trimming (FR-ENH-007, Gap 7 decision)
# Trim order: BRD → Adjacent reqs → Document structure → Intended use
# FRS spec and AC are never dropped.
# ---------------------------------------------------------------------------

def _apply_trim(ctx: RequirementContext, budget: int) -> RequirementContext:
    """Trim optional context components until the package fits within budget."""
    def _size(c: RequirementContext) -> int:
        parts = [
            c.requirement_text, c.frs_specification, c.acceptance_criteria,
            c.section_heading, c.intended_use_statement,
            " ".join(c.adjacent_prev), " ".join(c.adjacent_next),
        ]
        return _estimate_tokens(" ".join(p for p in parts if p))

    # BRD content is not directly in RequirementContext — it feeds AC.
    # If over budget, trim in order: adjacent → section heading → intended use.
    if _size(ctx) <= budget:
        return ctx

    # Step 1: drop adjacent requirements
    ctx.adjacent_prev = []
    ctx.adjacent_next = []
    if _size(ctx) <= budget:
        return ctx

    # Step 2: drop document structure context
    ctx.section_heading = ""
    if _size(ctx) <= budget:
        return ctx

    # Step 3: drop intended use statement (FRS and AC are never dropped)
    ctx.intended_use_statement = ""
    ctx.iu_ref = ""
    return ctx


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_all_context_packages(
    urs_text: str,
    frs_text: str,
    brd_text: str,
    sap_data: dict,
    pra_data: dict,
    metadata: ProjectMetadata,
) -> list[RequirementContext]:
    """
    Build one RequirementContext per URS/BRD requirement.
    Called once before STP/UTR generation begins.
    """
    urs_reqs = _extract_requirements_with_positions(urs_text, "URS")
    brd_reqs = _extract_requirements_with_positions(brd_text, "BRD") if brd_text else []
    all_reqs = urs_reqs + brd_reqs

    frs_sections = _split_frs_into_sections(frs_text)
    intended_uses: list[str] = sap_data.get("intended_uses", [])
    risk_classifications: list[dict] = pra_data.get("risk_classifications", [])

    packages: list[RequirementContext] = []

    for req in all_reqs:
        # Adjacent requirements (2 before, 2 after)
        idx = req.position
        source_list = urs_reqs if req.source == "URS" else brd_reqs
        adj_prev = [r.text for r in source_list[max(0, idx - 2):idx]]
        adj_next = [r.text for r in source_list[idx + 1:idx + 3]]

        # FRS match
        frs_content, link_type = _find_frs_match(req.text, req.req_id, frs_sections)

        # Acceptance criteria
        ac_text, ac_source = _extract_acceptance_criteria(frs_content, brd_text)

        # SAP intended use
        iu_text, iu_ref = _find_intended_use(req.text, intended_uses)

        # PRA risk classification
        risk_class, risk_rationale = _find_risk_classification(req.text, risk_classifications)

        ctx = RequirementContext(
            req_id=req.req_id,
            source_document=req.source,
            section_heading=req.section_heading,
            requirement_text=req.text,
            adjacent_prev=adj_prev,
            adjacent_next=adj_next,
            frs_specification=frs_content,
            frs_link_type=link_type,
            acceptance_criteria=ac_text,
            ac_source=ac_source,
            intended_use_statement=iu_text,
            iu_ref=iu_ref,
            risk_classification=risk_class,
            risk_rationale=risk_rationale,
        )

        ctx = _apply_trim(ctx, TOKEN_BUDGET)
        packages.append(ctx)

    return packages
