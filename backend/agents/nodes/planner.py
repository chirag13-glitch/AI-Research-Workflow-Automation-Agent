"""Planner node for LangGraph research workflow."""
from datetime import datetime
from backend.agents.state import ResearchAgentState
from backend.services.llm_adapter import llm_adapter
from backend.models.schemas import TaskStatus


async def planner_node(state: ResearchAgentState) -> ResearchAgentState:
    """
    Generate structured research plan:
    - objectives
    - subquestions
    - initial seed queries
    - info requirements
    - expected sections
    """
    topic = state.get("topic", "")
    constraints = state.get("constraints", [])

    try:
        plan = await llm_adapter.generate_plan(topic, constraints)
        plan_dict = plan.model_dump()
        subquestions = plan.subquestions
        seed_queries = plan.search_queries

        log_entry = {
            "node": "planner",
            "status": "COMPLETED",
            "message": f"Generated plan with {len(subquestions)} subquestions and {len(seed_queries)} queries",
            "timestamp": datetime.utcnow().isoformat(),
        }

        return {
            **state,
            "status": TaskStatus.PLANNING.value,
            "plan": plan_dict,
            "subquestions": subquestions,
            "active_queries": seed_queries,
            "step_history": [*state.get("step_history", []), log_entry],
        }
    except Exception as e:
        error_log = {
            "node": "planner",
            "status": "FAILED",
            "message": f"Planner failed: {str(e)}",
            "timestamp": datetime.utcnow().isoformat(),
        }
        return {
            **state,
            "status": TaskStatus.FAILED.value,
            "errors": [*state.get("errors", []), str(e)],
            "step_history": [*state.get("step_history", []), error_log],
        }
