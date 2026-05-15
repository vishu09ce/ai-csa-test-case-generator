from dataclasses import dataclass, field


@dataclass
class ProjectMetadata:
    project_id: str
    system_name: str
    system_type: str
    gamp5_category: str = "Category 4"
    predicate_rules: str = "21 CFR Part 11, 21 CFR Parts 210/211"


@dataclass
class RequirementContext:
    req_id: str
    source_document: str          # URS / FRS / BRD
    section_heading: str
    requirement_text: str
    adjacent_prev: list[str] = field(default_factory=list)   # up to 2 preceding req texts
    adjacent_next: list[str] = field(default_factory=list)   # up to 2 following req texts
    frs_specification: str = ""
    frs_link_type: str = "explicit"                          # "explicit" or "inferred"
    acceptance_criteria: str = ""
    ac_source: str = "FRS"                                   # "FRS" / "BRD" / "missing"
    intended_use_statement: str = ""
    iu_ref: str = ""
    risk_classification: str = "High Process Risk"           # or "Not High Process Risk"
    risk_rationale: str = ""
