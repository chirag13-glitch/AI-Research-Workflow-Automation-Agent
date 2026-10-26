"""Source validator node: checks source authenticity, detects conflicts, and determines if approval is needed."""
from datetime import datetime
from typing import List
from backend.agents.state import ResearchAgentState
from backend.models.schemas import TaskStatus


async def source_validator_node(state: ResearchAgentState) -> ResearchAgentState:
    """
    Validate collected evidence:
    - Assess source variety and information density
    - Flag suspicious or untrusted sources
    - Determine if human approval is requested or required due to ambiguity
    """
    sources = state.get("collected_sources", {})
    evidence = state.get("evidence_chunks", [])
    require_human_approval = state.get("require_human_approval", False)
    approval_status = state.get("approval_status")

    conflicts: List[str] = []
    requires_approval = False
    approval_reason = None

    # Check for untrusted sources
    untrusted = [s["source_id"] for s in sources.values() if not s.get("is_trusted", True)]
    if untrusted:
        conflicts.append(f"Sources {untrusted} contained potential injection patterns and were sanitized.")

    # Check sufficiency: if fewer than 2 sources or no evidence
    if len(sources) < 2 or len(evidence) < 2:
        conflicts.append("Sparse evidence: fewer than 2 authoritative sources retrieved.")

    # Determine if approval is needed
    if approval_status == "APPROVED":
        requires_approval = False
        approval_reason = None
    elif require_human_approval:
        requires_approval = True
        approval_reason = "User requested manual review prior to report generation."
    elif len(conflicts) > 0 and len(sources) < 1:
        requires_approval = True
        approval_reason = "; ".join(conflicts)

    log_entry = {
        "node": "source_validator",
        "status": "COMPLETED",
        "message": f"Validated {len(sources)} sources. Requires approval: {requires_approval}.",
        "timestamp": datetime.utcnow().isoformat(),
    }

    return {
        **state,
        "status": TaskStatus.VALIDATING_SOURCES.value,
        "conflicting_evidence": conflicts,
        "requires_approval": requires_approval,
        "approval_reason": approval_reason,
        "step_history": [*state.get("step_history", []), log_entry],
    }
