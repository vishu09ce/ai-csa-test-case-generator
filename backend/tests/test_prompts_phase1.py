import pytest
from backend.src.prompts.requirement_context import RequirementContext, ProjectMetadata
from backend.src.prompts.system_prompt import build_system_prompt
from backend.src.prompts.few_shot_examples import FEW_SHOT_EXAMPLES
from backend.src.prompts.stp_prompt import build_stp_system_prompt, build_stp_user_prompt
from backend.src.prompts.utr_prompt import build_utr_system_prompt, build_utr_user_prompt

METADATA = ProjectMetadata(
    project_id="proj-001",
    system_name="TrackSure LIMS",
    system_type="LIMS",
    gamp5_category="Category 4",
    predicate_rules="21 CFR Part 11, 21 CFR Parts 210/211",
)

CTX_HIGH = RequirementContext(
    req_id="REQ-010",
    source_document="FRS",
    section_heading="4.1 Sample Login",
    requirement_text="The system shall assign a unique sample ID upon sample login.",
    adjacent_prev=["REQ-009: The system shall support batch login of up to 50 samples."],
    adjacent_next=["REQ-011: The system shall print a barcode label upon sample login."],
    frs_specification="On login the system assigns a unique incremental ID in format SMP-YYYYMMDD-NNN.",
    frs_link_type="explicit",
    acceptance_criteria="Sample ID is unique. Format matches SMP-YYYYMMDD-NNN.",
    ac_source="FRS",
    intended_use_statement="Provide sample tracking from login through disposal.",
    iu_ref="IU-003",
    risk_classification="High Process Risk",
    risk_rationale="Duplicate IDs would compromise sample integrity.",
)

CTX_LOW_RISK = RequirementContext(
    req_id="REQ-020",
    source_document="URS",
    section_heading="6.2 Dashboard",
    requirement_text="The system shall display a summary dashboard on login.",
    frs_specification="Dashboard shows pending samples count, recent activity, and system alerts.",
    frs_link_type="inferred",
    acceptance_criteria="",
    ac_source="missing",
    risk_classification="Not High Process Risk",
    risk_rationale="Dashboard is informational only — no data integrity impact.",
)


class TestSystemPrompt:
    def test_contains_all_seven_layers(self):
        prompt = build_system_prompt(METADATA, "STP")
        for layer in ["LAYER 1", "LAYER 2", "LAYER 3", "LAYER 4", "LAYER 5", "LAYER 6", "LAYER 7"]:
            assert layer in prompt

    def test_stp_uses_four_step_cot(self):
        prompt = build_system_prompt(METADATA, "STP")
        assert "State the most foreseeable failure mode" in prompt
        assert "State the consequence" in prompt
        assert "Identify the system state" in prompt
        assert "Derive the expected result" in prompt

    def test_utr_uses_three_step_cot(self):
        prompt = build_system_prompt(METADATA, "UTR")
        assert "normal use pattern" in prompt
        assert "boundary conditions" in prompt
        assert "error states" in prompt
        assert "State the most foreseeable failure mode" not in prompt

    def test_layer_7_populated_with_metadata(self):
        prompt = build_system_prompt(METADATA, "STP")
        assert "TrackSure LIMS" in prompt
        assert "LIMS" in prompt
        assert "Category 4" in prompt

    def test_prohibited_behaviors_present(self):
        prompt = build_system_prompt(METADATA, "STP")
        assert "NEVER" in prompt
        assert "passive voice" in prompt


class TestFewShotExamples:
    def test_all_four_examples_present(self):
        assert "EXAMPLE 1" in FEW_SHOT_EXAMPLES
        assert "EXAMPLE 2" in FEW_SHOT_EXAMPLES
        assert "EXAMPLE 3" in FEW_SHOT_EXAMPLES
        assert "EXAMPLE 4" in FEW_SHOT_EXAMPLES

    def test_multi_acceptance_criteria_example(self):
        assert "MULTI_ACCEPTANCE_CRITERIA" in FEW_SHOT_EXAMPLES

    def test_low_confidence_example(self):
        assert "AMBIGUOUS_REQUIREMENT" in FEW_SHOT_EXAMPLES
        assert "MISSING_FRS_SPEC" in FEW_SHOT_EXAMPLES


class TestStpUserPrompt:
    def test_contains_requirement_id(self):
        prompt = build_stp_user_prompt(CTX_HIGH)
        assert "REQ-010" in prompt

    def test_contains_frs_specification(self):
        prompt = build_stp_user_prompt(CTX_HIGH)
        assert "SMP-YYYYMMDD-NNN" in prompt

    def test_contains_acceptance_criteria(self):
        prompt = build_stp_user_prompt(CTX_HIGH)
        assert "Sample ID is unique" in prompt

    def test_contains_risk_classification(self):
        prompt = build_stp_user_prompt(CTX_HIGH)
        assert "High Process Risk" in prompt

    def test_contains_adjacent_requirements(self):
        prompt = build_stp_user_prompt(CTX_HIGH)
        assert "REQ-009" in prompt
        assert "REQ-011" in prompt

    def test_contains_few_shot_examples(self):
        prompt = build_stp_user_prompt(CTX_HIGH)
        assert "FEW-SHOT EXAMPLES" in prompt

    def test_missing_frs_handled_gracefully(self):
        ctx = RequirementContext(
            req_id="REQ-099",
            source_document="URS",
            section_heading="",
            requirement_text="The system shall be fast.",
            risk_classification="High Process Risk",
        )
        prompt = build_stp_user_prompt(ctx)
        assert "No FRS specification found" in prompt

    def test_stp_system_prompt_uses_stp_cot(self):
        prompt = build_stp_system_prompt(METADATA)
        assert "State the most foreseeable failure mode" in prompt


class TestUtrUserPrompt:
    def test_contains_requirement_id(self):
        prompt = build_utr_user_prompt(CTX_LOW_RISK)
        assert "REQ-020" in prompt

    def test_contains_inferred_frs_label(self):
        prompt = build_utr_user_prompt(CTX_LOW_RISK)
        assert "inferred" in prompt

    def test_missing_ac_handled_gracefully(self):
        prompt = build_utr_user_prompt(CTX_LOW_RISK)
        assert "No acceptance criteria found" in prompt

    def test_utr_system_prompt_uses_utr_cot(self):
        prompt = build_utr_system_prompt(METADATA)
        assert "normal use pattern" in prompt
        assert "State the most foreseeable failure mode" not in prompt

    def test_contains_few_shot_examples(self):
        prompt = build_utr_user_prompt(CTX_LOW_RISK)
        assert "FEW-SHOT EXAMPLES" in prompt
