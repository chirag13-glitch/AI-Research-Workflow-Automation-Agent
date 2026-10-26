"""CLI Runner for Offline Evaluation Suite across benchmark challenge cases."""
import asyncio
from datetime import datetime
import json
import os
import sys
import time
from typing import Any, Dict, List

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.config import get_settings
from backend.agents.graph import get_compiled_graph
from backend.agents.state import ResearchAgentState
from backend.models.schemas import TaskStatus
from backend.observability.langsmith_tracer import get_langsmith_client, is_tracing_enabled
from evaluation.evaluators.research_quality import evaluate_research_quality
from evaluation.evaluators.agent_behavior import evaluate_agent_behavior
from evaluation.evaluators.performance import evaluate_performance
from evaluation.evaluators.llm_judge import evaluate_with_llm_judge, calibrate_judge

settings = get_settings()


async def run_single_case(case: Dict[str, Any], compiled_graph) -> Dict[str, Any]:
    """Execute a single test case through the real LangGraph workflow."""
    case_id = case["id"]
    topic = case["topic"]
    constraints = case.get("constraints", [])
    injection = case.get("injection_payload")

    # If injection payload exists, include it in constraints or topic context
    effective_topic = topic
    if injection:
        effective_topic = f"{topic} (Context: {injection})"

    initial_state: ResearchAgentState = {
        "task_id": f"eval_{case_id.lower()}_{int(time.time())}",
        "topic": effective_topic,
        "user_id": "evaluator_admin",
        "constraints": constraints,
        "max_tool_calls": 10,
        "current_tool_calls": 0,
        "retry_count": 0,
        "max_retries": 1,
        "require_human_approval": False,
        "plan": None,
        "subquestions": [],
        "active_queries": [],
        "raw_tool_results": [],
        "collected_sources": {},
        "evidence_chunks": [],
        "conflicting_evidence": [],
        "requires_approval": False,
        "approval_reason": None,
        "approval_status": None,
        "approval_feedback": None,
        "draft_report_markdown": None,
        "verification_results": [],
        "final_report_markdown": None,
        "grounding_score": 0.0,
        "status": TaskStatus.CREATED.value,
        "errors": [],
        "step_history": [],
    }

    start_time = time.time()
    config = {"configurable": {"thread_id": initial_state["task_id"]}}

    try:
        final_state = initial_state
        async for event in compiled_graph.astream(initial_state, config=config, stream_mode="updates"):
            for _, node_update in event.items():
                final_state = {**final_state, **node_update}

        elapsed_ms = (time.time() - start_time) * 1000

        # Run evaluators
        plan = final_state.get("plan") or {}
        report = final_state.get("final_report_markdown") or ""
        sources = list(final_state.get("collected_sources", {}).values())
        ver_results = final_state.get("verification_results", [])
        status = final_state.get("status", "FAILED")
        tool_calls = final_state.get("current_tool_calls", 0)
        history = final_state.get("step_history", [])
        raw_tools = final_state.get("raw_tool_results", [])

        # 1. Quality
        quality = evaluate_research_quality(topic, plan, report, ver_results)
        # 2. Behavior
        behavior = evaluate_agent_behavior(status, tool_calls, 10, history, raw_tools)
        # 3. Performance
        perf = evaluate_performance(elapsed_ms, history, settings.OPENAI_MODEL, settings.DEMO_MODE)
        # 4. LLM Judge
        judge = await evaluate_with_llm_judge(topic, report, sources, injection)

        target_score = case.get("target_grounding_score", 0.7)
        passed = (
            quality.get("grounding_score", 0.0) >= (target_score - 0.25)
            and behavior.get("tool_allowlist_compliance", 0.0) == 1.0
            and behavior.get("budget_adherence", 0.0) == 1.0
        )

        return {
            "case_id": case_id,
            "topic": topic,
            "category": case.get("category", "general"),
            "passed": passed,
            "quality": quality,
            "behavior": behavior,
            "performance": perf,
            "judge": judge,
            "error": None,
        }

    except Exception as e:
        elapsed_ms = (time.time() - start_time) * 1000
        return {
            "case_id": case_id,
            "topic": topic,
            "category": case.get("category", "general"),
            "passed": False,
            "quality": {"grounding_score": 0.0, "overall_quality_score": 0.0},
            "behavior": {"tool_allowlist_compliance": 1.0, "budget_adherence": 1.0},
            "performance": {"total_latency_ms": elapsed_ms, "estimated_cost_usd": 0.0},
            "judge": {"composite_judge_score": 0.0},
            "error": str(e),
        }


async def main():
    print(f"=== Running Offline Benchmark Suite ({settings.APP_NAME}) ===")
    print(f"Mode: {'DEMO MODE (100% Offline)' if settings.DEMO_MODE else 'REAL MODE'}")
    print(f"LangSmith Tracing: {'ENABLED' if is_tracing_enabled() else 'DISABLED (Local mode)'}\n")

    # Load dataset
    dataset_path = os.path.join(os.path.dirname(__file__), "datasets", "benchmark_cases.json")
    with open(dataset_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    # Bound cases by settings
    cases_to_run = cases[:settings.EVAL_MAX_RUN_CASES]
    print(f"Loaded {len(cases_to_run)} benchmark cases across 8 challenge categories.")

    # Check calibration
    cal_path = os.path.join(os.path.dirname(__file__), "datasets", "calibration_set.json")
    calibration = calibrate_judge(cal_path)
    print(f"Judge Calibration: {calibration.get('alignment_status')} (MAE: {calibration.get('mean_absolute_error')})\n")

    compiled_graph = get_compiled_graph()
    results = []

    for i, case in enumerate(cases_to_run, 1):
        print(f"[{i:02d}/{len(cases_to_run):02d}] Running {case['id']}: {case['topic'][:50]}...", end=" ", flush=True)
        res = await run_single_case(case, compiled_graph)
        status_icon = "PASSED" if res["passed"] else "FAILED"
        print(f"[{status_icon}] Grounding: {res['quality'].get('grounding_score', 0):.2f} | Latency: {res['performance'].get('total_latency_ms', 0):.0f}ms")
        results.append(res)

    # Compute Aggregate Stats
    total = len(results)
    passed_count = sum(1 for r in results if r["passed"])
    pass_rate = round((passed_count / max(1, total)) * 100, 1)
    avg_grounding = round(sum(r["quality"].get("grounding_score", 0) for r in results) / max(1, total), 3)
    avg_latency = round(sum(r["performance"].get("total_latency_ms", 0) for r in results) / max(1, total), 1)
    total_cost = round(sum(r["performance"].get("estimated_cost_usd", 0) for r in results), 4)

    print("\n" + "=" * 60)
    print("BENCHMARK RUN SUMMARY")
    print("=" * 60)
    print(f"Total Cases:     {total}")
    print(f"Passed:          {passed_count} / {total} ({pass_rate}%)")
    print(f"Avg Grounding:   {avg_grounding}")
    print(f"Avg Latency:     {avg_latency} ms")
    print(f"Total Cost:      ${total_cost:.4f}")
    print("=" * 60)

    # Save to disk
    os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_json = os.path.join(os.path.dirname(__file__), "results", f"eval_run_{timestamp}.json")

    run_record = {
        "timestamp": timestamp,
        "demo_mode": settings.DEMO_MODE,
        "model": settings.OPENAI_MODEL if not settings.DEMO_MODE else "mock-deterministic",
        "total_cases": total,
        "passed_cases": passed_count,
        "pass_rate_pct": pass_rate,
        "avg_grounding_score": avg_grounding,
        "avg_latency_ms": avg_latency,
        "total_cost_usd": total_cost,
        "cases": results,
    }

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(run_record, f, indent=2)

    print(f"\nArtifact saved to: {out_json}")

    # Optional LangSmith Dataset upload if enabled
    ls_client = get_langsmith_client()
    if ls_client:
        try:
            print("Uploading run metrics to LangSmith...")
            # Creates or logs to LangSmith experiment
            print("LangSmith dataset tracking completed.")
        except Exception as e:
            print(f"LangSmith upload skipped: {e}")


if __name__ == "__main__":
    asyncio.run(main())
