import pytest
from backend.src.services.rag_service import (
    _extract_requirements_with_positions,
    _split_frs_into_sections,
    _find_frs_match,
    _extract_acceptance_criteria,
    _find_intended_use,
    _find_risk_classification,
    _apply_trim,
    build_all_context_packages,
    SEMANTIC_THRESHOLD,
)
from backend.src.prompts.requirement_context import RequirementContext, ProjectMetadata

URS_TEXT = """\
3.1 Sample Login
REQ-001: The system shall assign a unique sample ID upon sample login.
REQ-002: The system shall print a barcode label upon sample login.
REQ-003: The system shall support batch login of up to 50 samples.

3.2 Sample Tracking
REQ-004: The system shall track sample location throughout the laboratory.
REQ-005: The system shall record chain of custody for each sample transfer.
"""

FRS_TEXT = """\
4.1 Sample Login Specification
On login the system assigns a unique incremental ID in format SMP-YYYYMMDD-NNN. REQ-001.
The system shall: (1) generate barcode; (2) print label automatically.
Acceptance criteria: Sample ID is unique and matches format SMP-YYYYMMDD-NNN.

4.2 Batch Login
The system supports batch processing of up to 50 samples per session.
"""

BRD_TEXT = "The application shall provide sample login with unique identifiers for traceability."

SAP_DATA = {
    "intended_uses": [
        "Provide sample tracking from login through disposal.",
        "Support regulatory compliance with 21 CFR Part 11.",
        "Enable chain of custody recording for all sample transfers.",
    ]
}

PRA_DATA = {
    "risk_classifications": [
        {"feature": "Sample login and ID assignment", "risk_classification": "High Process Risk",
         "rationale": "Duplicate IDs compromise sample integrity."},
        {"feature": "Sample location tracking", "risk_classification": "Not High Process Risk",
         "rationale": "Loss of location data is recoverable."},
    ]
}

METADATA = ProjectMetadata(
    project_id="proj-001",
    system_name="TrackSure LIMS",
    system_type="LIMS",
)


class TestRequirementExtraction:
    def test_extracts_correct_count(self):
        reqs = _extract_requirements_with_positions(URS_TEXT, "URS")
        assert len(reqs) == 5

    def test_extracts_req_ids(self):
        reqs = _extract_requirements_with_positions(URS_TEXT, "URS")
        ids = [r.req_id for r in reqs]
        assert "REQ-001" in ids
        assert "REQ-005" in ids

    def test_extracts_section_heading(self):
        reqs = _extract_requirements_with_positions(URS_TEXT, "URS")
        req1 = next(r for r in reqs if r.req_id == "REQ-001")
        assert "Sample Login" in req1.section_heading

    def test_position_is_sequential(self):
        reqs = _extract_requirements_with_positions(URS_TEXT, "URS")
        assert [r.position for r in reqs] == list(range(len(reqs)))

    def test_empty_text_returns_empty(self):
        assert _extract_requirements_with_positions("", "URS") == []


class TestFrsSectionSplitting:
    def test_splits_into_multiple_sections(self):
        sections = _split_frs_into_sections(FRS_TEXT)
        assert len(sections) >= 2

    def test_section_headings_captured(self):
        sections = _split_frs_into_sections(FRS_TEXT)
        headings = [s.heading for s in sections]
        assert any("Sample Login" in h for h in headings)

    def test_fallback_to_single_section_for_unstructured_text(self):
        sections = _split_frs_into_sections("No headings here just text.")
        assert len(sections) == 1


class TestFrsMatching:
    def test_explicit_match_by_req_id(self):
        sections = _split_frs_into_sections(FRS_TEXT)
        content, link_type = _find_frs_match("unique sample ID", "REQ-001", sections)
        assert link_type == "explicit"
        assert "SMP-YYYYMMDD-NNN" in content

    def test_inferred_match_above_threshold(self):
        sections = _split_frs_into_sections(FRS_TEXT)
        # REQ-003 not mentioned by ID in FRS but text about batch login matches
        content, link_type = _find_frs_match(
            "batch login up to 50 samples session", "REQ-003", sections
        )
        assert link_type in ("inferred", "explicit")

    def test_missing_when_no_match(self):
        sections = _split_frs_into_sections(FRS_TEXT)
        content, link_type = _find_frs_match(
            "completely unrelated topic about invoicing", "REQ-999", sections
        )
        assert link_type == "missing"
        assert content == ""

    def test_empty_frs_returns_missing(self):
        content, link_type = _find_frs_match("any requirement", "REQ-001", [])
        assert link_type == "missing"


class TestAcceptanceCriteriaExtraction:
    def test_extracts_from_frs(self):
        ac, source = _extract_acceptance_criteria(
            "Acceptance criteria: Sample ID is unique and format matches SMP-YYYYMMDD-NNN.", ""
        )
        assert source == "FRS"
        assert "unique" in ac.lower()

    def test_falls_back_to_brd(self):
        ac, source = _extract_acceptance_criteria(
            "No AC here.", "Acceptance criteria: traceability required."
        )
        assert source == "BRD"

    def test_returns_missing_when_none_found(self):
        ac, source = _extract_acceptance_criteria("Just a description.", "")
        assert source == "missing"
        assert ac == ""


class TestIntendedUseMatching:
    def test_returns_best_match(self):
        iu, ref = _find_intended_use("sample login unique ID assignment", SAP_DATA["intended_uses"])
        assert iu != ""
        assert ref.startswith("IU-")

    def test_returns_empty_when_no_uses(self):
        iu, ref = _find_intended_use("some requirement", [])
        assert iu == ""
        assert ref == ""


class TestRiskClassification:
    def test_high_risk_matched(self):
        risk, rationale = _find_risk_classification(
            "assign unique sample ID login", PRA_DATA["risk_classifications"]
        )
        assert risk == "High Process Risk"

    def test_not_high_risk_matched(self):
        risk, rationale = _find_risk_classification(
            "track sample location laboratory", PRA_DATA["risk_classifications"]
        )
        assert risk == "Not High Process Risk"

    def test_defaults_when_empty_pra(self):
        risk, rationale = _find_risk_classification("any requirement", [])
        assert risk == "Not High Process Risk"


class TestTokenTrimming:
    def _make_ctx(self, **kwargs):
        defaults = dict(
            req_id="REQ-001", source_document="URS", section_heading="3.1 Login",
            requirement_text="The system shall assign a unique ID.",
            adjacent_prev=["REQ-000: Previous requirement text here."],
            adjacent_next=["REQ-002: Following requirement text here."],
            frs_specification="FRS: system assigns unique ID format SMP-NNN.",
            frs_link_type="explicit",
            acceptance_criteria="AC: ID is unique.",
            ac_source="FRS",
            intended_use_statement="Provide sample tracking.",
            iu_ref="IU-001",
            risk_classification="High Process Risk",
            risk_rationale="Duplicate IDs compromise integrity.",
        )
        defaults.update(kwargs)
        return RequirementContext(**defaults)

    def test_no_trim_when_under_budget(self):
        ctx = self._make_ctx()
        result = _apply_trim(ctx, budget=9999)
        assert result.adjacent_prev != [] or result.section_heading != "" or result.intended_use_statement != ""

    def test_adjacent_dropped_when_over_budget(self):
        ctx = self._make_ctx(
            adjacent_prev=["x" * 5000],
            adjacent_next=["y" * 5000],
        )
        result = _apply_trim(ctx, budget=100)
        assert result.adjacent_prev == []
        assert result.adjacent_next == []

    def test_frs_never_dropped(self):
        ctx = self._make_ctx(
            frs_specification="Critical FRS content " * 200,
            adjacent_prev=["x" * 5000],
        )
        result = _apply_trim(ctx, budget=50)
        assert result.frs_specification != ""

    def test_ac_never_dropped(self):
        ctx = self._make_ctx(
            acceptance_criteria="Critical AC content " * 200,
            adjacent_prev=["x" * 5000],
        )
        result = _apply_trim(ctx, budget=50)
        assert result.acceptance_criteria != ""


class TestBuildAllContextPackages:
    def test_returns_one_package_per_requirement(self):
        packages = build_all_context_packages(
            URS_TEXT, FRS_TEXT, BRD_TEXT, SAP_DATA, PRA_DATA, METADATA
        )
        assert len(packages) == 5

    def test_each_package_has_req_id(self):
        packages = build_all_context_packages(
            URS_TEXT, FRS_TEXT, BRD_TEXT, SAP_DATA, PRA_DATA, METADATA
        )
        ids = [p.req_id for p in packages]
        assert "REQ-001" in ids

    def test_risk_classification_populated(self):
        packages = build_all_context_packages(
            URS_TEXT, FRS_TEXT, BRD_TEXT, SAP_DATA, PRA_DATA, METADATA
        )
        for pkg in packages:
            assert pkg.risk_classification in ("High Process Risk", "Not High Process Risk")

    def test_empty_brd_handled(self):
        packages = build_all_context_packages(
            URS_TEXT, FRS_TEXT, "", SAP_DATA, PRA_DATA, METADATA
        )
        assert len(packages) == 5

    def test_no_urs_requirements_returns_empty(self):
        packages = build_all_context_packages(
            "No requirements here.", FRS_TEXT, "", SAP_DATA, PRA_DATA, METADATA
        )
        assert packages == []
