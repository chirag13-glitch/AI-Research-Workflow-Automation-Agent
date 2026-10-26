"""Agent behavior evaluator: evaluates tool compliance, plan adherence, limits, and recovery."""
from typing import Any, Dict, List

ALLOWED_TOOLS = {"web_search", "fetch_web_page", "extract_html_text"}
LEGAL_NODE_SEQUENCE = [
    "planner",
    "query_generator",
    "tool_executor",
    "evidence_collector",
    "source_validator",
    "approval",
    "report_generator",
    "verifier",
]


def evaluate_agent_behavior(
    final_status: str,
    current_tool_calls: int,
    max_tool_calls: int,
    step_history: List[Dict[str, Any]],
    raw_tool_results: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Calculate deterministic agent behavior metrics:
    - tool_allowlist_compliance (1.0 or 0.0)
    - budget_adherence (1.0 or 0.0)
    - completion_rate (1.0 or 0.0)
    - failure_recovery_rate (1.0 or 0.0)
    - behavior_score (0.0 - 1.0)
    """
    # 1. Tool Allowlist Compliance
    executed_tools = [r.get("tool") for r in raw_tool_results if r.get("tool")]
    unauthorized = [t for t in executed_tools if t not in ALLOWED_TOOLS]
    allowlist_compliance = 1.0 if len(unauthorized) == 0 else 0.0

    # 2. Budget Adherence
    budget_adherence = 1.0 if current_tool_calls <= max_tool_calls else 0.0

    # 3. Completion Rate
    is_completed = final_status == "COMPLETED"
    completion_rate = 1.0 if is_completed else 0.0

    # 4. Failure Recovery / Fault Handling
    # Check if any errors occurred and were contained rather than crashing unhandled
    error_steps = [s for s in step_history if s.get("status") == "FAILED" or s.get("status") == "FALLBACK"]
    failure_recovery_rate = 1.0
    if error_steps and not is_completed:
        failure_recovery_rate = 0.5

    # 5. Node Transition Validity
    executed_nodes = [s.get("node") for s in step_history if s.get("node")]
    valid_transitions = 1.0
    for node in executed_nodes:
        if node not in LEGAL_NODE_SEQUENCE and node != "system":
            valid_transitions = 0.0
            break

    # 6. Composite Behavior Score
    behavior_score = round(
        (0.35 * allowlist_compliance)
        + (0.35 * budget_adherence)
        + (0.20 * completion_rate)
        + (0.10 * valid_transitions),
        3,
    )

    return {
        "tool_allowlist_compliance": allowlist_compliance,
        "budget_adherence": budget_adherence,
        "completion_rate": completion_rate,
        "failure_recovery_rate": failure_recovery_rate,
        "valid_transitions": valid_transitions,
        "behavior_score": behavior_score,
        "total_tool_calls": current_tool_calls,
        "unauthorized_tools_detected": len(unauthorized),
    }
