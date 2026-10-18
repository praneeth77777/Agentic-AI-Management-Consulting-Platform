from app.graph.workflow import new_state
from app.models.contracts import GraphState


def test_new_state_contains_question():
    state = new_state("What operational risks does Cisco disclose?")

    assert state["question"] == (
        "What operational risks does Cisco disclose?"
    )
    assert state["request_id"]


def test_graph_state_round_trip():
    raw_state = new_state(
        "What operational risks does Cisco disclose?"
    )

    state = GraphState.model_validate(raw_state)

    assert state.question == (
        "What operational risks does Cisco disclose?"
    )