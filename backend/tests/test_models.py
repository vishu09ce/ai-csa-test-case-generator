import pytest
from backend.src.models.project import Project, ProjectState, STATE_TRANSITIONS


def test_project_initial_state():
    p = Project(name="Test", system_type="LIMS")
    assert p.state == ProjectState.DRAFT


def test_project_is_editable_in_draft():
    p = Project(name="Test", system_type="LIMS")
    assert p.is_editable() is True


def test_project_not_editable_after_draft():
    p = Project(name="Test", system_type="LIMS")
    p.state = ProjectState.SAP_REVIEW
    assert p.is_editable() is False


def test_state_advances_forward():
    p = Project(name="Test", system_type="LIMS")
    p.advance_state()
    assert p.state == ProjectState.SAP_REVIEW


def test_full_state_sequence():
    p = Project(name="Test", system_type="LIMS")
    expected = [
        ProjectState.SAP_REVIEW,
        ProjectState.PRA_REVIEW,
        ProjectState.RTM_REVIEW,
        ProjectState.PROTOCOL_REVIEW,
        ProjectState.EXECUTION,
        ProjectState.SUMMARY_REVIEW,
        ProjectState.COMPLETE,
    ]
    for state in expected:
        p.advance_state()
        assert p.state == state


def test_advance_from_complete_raises():
    p = Project(name="Test", system_type="LIMS")
    p.state = ProjectState.COMPLETE
    with pytest.raises(ValueError, match="terminal state"):
        p.advance_state()


def test_state_transitions_cover_all_non_terminal_states():
    non_terminal = [s for s in ProjectState if s != ProjectState.COMPLETE]
    for state in non_terminal:
        assert state in STATE_TRANSITIONS, f"Missing transition for {state}"
