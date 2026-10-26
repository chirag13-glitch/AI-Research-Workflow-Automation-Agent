"""Tool executor node: executes allowlisted search and fetch tools with budget enforcement."""
import asyncio
from datetime import datetime
from typing import List, Dict, Any
from backend.agents.state import ResearchAgentState
from backend.tools.registry import tool_registry, ToolExecutionBudgetExceeded
from backend.models.schemas import TaskStatus


async def tool_executor_node(state: ResearchAgentState) -> ResearchAgentState:
    """
    Execute searches for active queries, followed by page fetches for discovered URLs.
    Enforces budget limits and handles individual tool failures gracefully.
    """
    queries = state.get("active_queries", [])
    current_calls = state.get("current_tool_calls", 0)
    max_calls = state.get("max_tool_calls", 15)
    existing_raw = state.get("raw_tool_results", [])

    new_raw_results: List[Dict[str, Any]] = []
    urls_to_fetch: List[str] = []

    # Step 1: Execute Searches
    for q in queries[:2]:  # Bound search queries per cycle
        if current_calls >= max_calls:
            break
        try:
            res = await tool_registry.execute(
                tool_name="web_search",
                kwargs={"query": q, "max_results": 3},
                current_calls=current_calls,
                max_calls=max_calls,
            )
            current_calls += 1
            if res.get("success") and res.get("result"):
                search_items = res["result"]
                new_raw_results.append({
                    "tool": "web_search",
                    "query": q,
                    "items": search_items,
                })
                for item in search_items:
                    u = item.get("url")
                    if u and u not in urls_to_fetch:
                        urls_to_fetch.append(u)
        except ToolExecutionBudgetExceeded:
            break
        except Exception as e:
            new_raw_results.append({
                "tool": "web_search",
                "query": q,
                "error": str(e),
            })

    # Step 2: Fetch pages for discovered URLs (up to 3 pages per step to avoid unbounded fetches)
    for u in urls_to_fetch[:3]:
        if current_calls >= max_calls:
            break
        try:
            res = await tool_registry.execute(
                tool_name="fetch_web_page",
                kwargs={"url": u, "timeout_seconds": 8},
                current_calls=current_calls,
                max_calls=max_calls,
            )
            current_calls += 1
            if res.get("success") and res.get("result"):
                new_raw_results.append({
                    "tool": "fetch_web_page",
                    "url": u,
                    "data": res["result"],
                })
        except ToolExecutionBudgetExceeded:
            break
        except Exception as e:
            new_raw_results.append({
                "tool": "fetch_web_page",
                "url": u,
                "error": str(e),
            })

    log_entry = {
        "node": "tool_executor",
        "status": "COMPLETED",
        "message": f"Executed tool batch. Budget: {current_calls}/{max_calls} calls.",
        "timestamp": datetime.utcnow().isoformat(),
    }

    return {
        **state,
        "status": TaskStatus.COLLECTING_EVIDENCE.value,
        "current_tool_calls": current_calls,
        "raw_tool_results": [*existing_raw, *new_raw_results],
        "step_history": [*state.get("step_history", []), log_entry],
    }
