"""LangGraph StateGraph definition, conditional edges, and compiled workflow."""
from langgraph.graph import StateGraph, START, END
from backend.agents.state import ResearchAgentState
from backend.agents.nodes.planner import planner_node
from backend.agents.nodes.query_generator import query_generator_node
from backend.agents.nodes.tool_executor import tool_executor_node
from backend.agents.nodes.evidence_collector import evidence_collector_node
from backend.agents.nodes.source_validator import source_validator_node
from backend.agents.nodes.approval import approval_node
from backend.agents.nodes.report_generator import report_generator_node
from backend.agents.nodes.verifier import verifier_node
from backend.db.checkpointer import get_checkpointer
from backend.models.schemas import TaskStatus


def route_after_validator(state: ResearchAgentState) -> str:
    """Route to approval gate if required; otherwise proceed directly to report generation."""
    if state.get("requires_approval", False) and state.get("approval_status") != "APPROVED":
        return "approval"
    return "report_generator"


def route_after_approval(state: ResearchAgentState) -> str:
    """If approved, proceed to report generation; otherwise end paused."""
    if state.get("approval_status") == "APPROVED":
        return "report_generator"
    return END


def route_after_verifier(state: ResearchAgentState) -> str:
    """If verifier requested retry and retry budget remains, loop back to query generator."""
    if state.get("status") == TaskStatus.COLLECTING_EVIDENCE.value:
        return "query_generator"
    return END


def build_research_graph() -> StateGraph:
    """Construct the bounded LangGraph state machine."""
    workflow = StateGraph(ResearchAgentState)

    # Register Nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("query_generator", query_generator_node)
    workflow.add_node("tool_executor", tool_executor_node)
    workflow.add_node("evidence_collector", evidence_collector_node)
    workflow.add_node("source_validator", source_validator_node)
    workflow.add_node("approval", approval_node)
    workflow.add_node("report_generator", report_generator_node)
    workflow.add_node("verifier", verifier_node)

    # Linear Transitions
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "query_generator")
    workflow.add_edge("query_generator", "tool_executor")
    workflow.add_edge("tool_executor", "evidence_collector")
    workflow.add_edge("evidence_collector", "source_validator")

    # Conditional Transitions
    workflow.add_conditional_edges(
        "source_validator",
        route_after_validator,
        {
            "approval": "approval",
            "report_generator": "report_generator",
        },
    )

    workflow.add_conditional_edges(
        "approval",
        route_after_approval,
        {
            "report_generator": "report_generator",
            END: END,
        },
    )

    workflow.add_edge("report_generator", "verifier")

    workflow.add_conditional_edges(
        "verifier",
        route_after_verifier,
        {
            "query_generator": "query_generator",
            END: END,
        },
    )

    return workflow


_compiled_graph = None


def get_compiled_graph():
    """Return the cached compiled LangGraph with active checkpointer."""
    global _compiled_graph
    if _compiled_graph is None:
        checkpointer = get_checkpointer()
        graph_def = build_research_graph()
        _compiled_graph = graph_def.compile(checkpointer=checkpointer)
    return _compiled_graph
