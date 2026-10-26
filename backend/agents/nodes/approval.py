"""Human approval node: pauses task in AWAITING_APPROVAL state for authorized user review."""
from datetime import datetime
from backend.agents.state import ResearchAgentState
from backend.models.schemas import TaskStatus


async def approval_node(state: ResearchAgentState) -> ResearchAgentState:
    """
    Pause execution for human-in-the-loop approval.
    If already approved by user via API, pass through; otherwise set state to AWAITING_APPROVAL.
    """
    approval_status = state.get("approval_status")

    if approval_status == "APPROVED":
        log_entry = {
            "node": "approval",
            "status": "APPROVED",
            "message": f"Task resumed after user approval. Feedback: {state.get('approval_feedback', 'None')}",
            "timestamp": datetime.utcnow().isoformat(),
        }
        return {
            **state,
            "requires_approval": False,
            "status": TaskStatus.VALIDATING_SOURCES.value,
            "step_history": [*state.get("step_history", []), log_entry],
        }

    # Otherwise mark task as waiting for approval
    log_entry = {
        "node": "approval",
        "status": "PAUSED",
        "message": f"Paused: {state.get('approval_reason', 'Awaiting human authorization')}",
        "timestamp": datetime.utcnow().isoformat(),
    }

    return {
        **state,
        "status": TaskStatus.AWAITING_APPROVAL.value,
        "step_history": [*state.get("step_history", []), log_entry],
    }
