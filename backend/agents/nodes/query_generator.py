"""Query generator node: produces targeted search queries based on plan and evidence gaps."""
from datetime import datetime
from backend.agents.state import ResearchAgentState
from backend.services.llm_adapter import llm_adapter


async def query_generator_node(state: ResearchAgentState) -> ResearchAgentState:
    """
    Generate or refine search queries based on active subquestions
    and any feedback or gaps identified in verification.
    """
    topic = state.get("topic", "")
    subquestions = state.get("subquestions", [])
    current_queries = state.get("active_queries", [])
    collected_sources = state.get("collected_sources", {})

    # If we already have seed queries and no sources yet, keep the seed queries
    if current_queries and not collected_sources:
        return state

    # Otherwise, pick next unanswered subquestion and generate targeted queries
    next_question = subquestions[0] if subquestions else topic
    prior_titles = [s.get("title", "") for s in collected_sources.values()]

    try:
        new_queries = await llm_adapter.generate_queries(topic, next_question, prior_titles)
        log_entry = {
            "node": "query_generator",
            "status": "COMPLETED",
            "message": f"Generated {len(new_queries)} refined search queries for subquestion: {next_question[:60]}...",
            "timestamp": datetime.utcnow().isoformat(),
        }
        return {
            **state,
            "active_queries": new_queries,
            "step_history": [*state.get("step_history", []), log_entry],
        }
    except Exception as e:
        log_entry = {
            "node": "query_generator",
            "status": "FALLBACK",
            "message": f"Query generation fallback: {str(e)}",
            "timestamp": datetime.utcnow().isoformat(),
        }
        fallback_queries = [f"{topic} analysis", f"{topic} benchmark evidence"]
        return {
            **state,
            "active_queries": fallback_queries,
            "step_history": [*state.get("step_history", []), log_entry],
        }
