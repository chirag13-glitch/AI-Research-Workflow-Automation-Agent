"""Performance evaluator: latency profiling, token usage estimation, and cost accounting."""
from typing import Any, Dict, List


def evaluate_performance(
    total_elapsed_ms: float,
    step_history: List[Dict[str, Any]],
    model_name: str = "gpt-4o",
    is_demo_mode: bool = True,
) -> Dict[str, Any]:
    """
    Profile execution latency and compute cost metrics:
    - total_latency_ms
    - per_stage_latency_ms
    - estimated_prompt_tokens
    - estimated_completion_tokens
    - estimated_cost_usd
    """
    # Breakdown latency roughly across steps
    step_count = max(1, len(step_history))
    avg_step_latency = round(total_elapsed_ms / step_count, 2)
    per_stage_latency = {
        s.get("node", f"step_{i}"): avg_step_latency for i, s in enumerate(step_history)
    }

    # Estimate tokens based on typical LangGraph prompt and report synthesis sizes
    # In a full run: ~2,500 prompt tokens (plan + query gen + evidence) and ~1,200 completion tokens
    estimated_prompt_tokens = 2500
    estimated_completion_tokens = 1200
    total_tokens = estimated_prompt_tokens + estimated_completion_tokens

    # Standard GPT-4o pricing: $2.50 / 1M prompt, $10.00 / 1M completion
    # In Demo Mode: $0.00
    if is_demo_mode:
        estimated_cost_usd = 0.0
    else:
        prompt_cost = (estimated_prompt_tokens / 1_000_000) * 2.50
        comp_cost = (estimated_completion_tokens / 1_000_000) * 10.00
        estimated_cost_usd = round(prompt_cost + comp_cost, 5)

    return {
        "total_latency_ms": round(total_elapsed_ms, 2),
        "per_stage_latency_ms": per_stage_latency,
        "estimated_prompt_tokens": estimated_prompt_tokens,
        "estimated_completion_tokens": estimated_completion_tokens,
        "total_tokens": total_tokens,
        "estimated_cost_usd": estimated_cost_usd,
    }
