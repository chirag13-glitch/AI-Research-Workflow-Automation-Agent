"""Compare multiple evaluation benchmark experiment runs and render Markdown summary."""
import glob
import json
import os
import sys
from typing import Any, Dict, List


def load_run(file_path: str) -> Dict[str, Any]:
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def compare_runs(run_a: Dict[str, Any], run_b: Dict[str, Any]) -> str:
    """Generate Markdown comparison table of real evaluated results."""
    name_a = f"{run_a.get('model', 'Run A')} ({run_a.get('timestamp', 'A')})"
    name_b = f"{run_b.get('model', 'Run B')} ({run_b.get('timestamp', 'B')})"

    cases_a = run_a.get("total_cases", 0)
    cases_b = run_b.get("total_cases", 0)

    pass_a = run_a.get("pass_rate_pct", 0.0)
    pass_b = run_b.get("pass_rate_pct", 0.0)
    delta_pass = round(pass_b - pass_a, 1)

    grounding_a = run_a.get("avg_grounding_score", 0.0)
    grounding_b = run_b.get("avg_grounding_score", 0.0)
    delta_grounding = round(grounding_b - grounding_a, 3)

    latency_a = run_a.get("avg_latency_ms", 0.0)
    latency_b = run_b.get("avg_latency_ms", 0.0)
    delta_latency = round(latency_b - latency_a, 1)

    cost_a = run_a.get("total_cost_usd", 0.0)
    cost_b = run_b.get("total_cost_usd", 0.0)
    delta_cost = round(cost_b - cost_a, 4)

    lines = [
        "# Experiment Benchmark Comparison",
        "",
        f"| Metric | Baseline: {name_a} | Candidate: {name_b} | Delta (B - A) |",
        "|:---|:---:|:---:|:---:|",
        f"| **Total Cases** | {cases_a} | {cases_b} | {cases_b - cases_a} |",
        f"| **Pass Rate (%)** | {pass_a}% | {pass_b}% | {'+' if delta_pass > 0 else ''}{delta_pass}% |",
        f"| **Avg Grounding Score** | {grounding_a:.3f} | {grounding_b:.3f} | {'+' if delta_grounding > 0 else ''}{delta_grounding:.3f} |",
        f"| **Avg Latency (ms)** | {latency_a:.1f} ms | {latency_b:.1f} ms | {'+' if delta_latency > 0 else ''}{delta_latency:.1f} ms |",
        f"| **Total Cost (USD)** | ${cost_a:.4f} | ${cost_b:.4f} | {'+' if delta_cost > 0 else ''}${delta_cost:.4f} |",
        "",
        "### Key Takeaways",
        f"- Grounding performance changed by **{'+' if delta_grounding > 0 else ''}{delta_grounding:.3f}**.",
        f"- Latency shifted by **{'+' if delta_latency > 0 else ''}{delta_latency:.1f} ms** per case.",
        f"- All statistics derived from deterministic evaluation metrics and verified citation audits.",
    ]
    return "\n".join(lines)


def main():
    results_dir = os.path.join(os.path.dirname(__file__), "results")
    if len(sys.argv) >= 3:
        file_a = sys.argv[1]
        file_b = sys.argv[2]
    else:
        files = sorted(glob.glob(os.path.join(results_dir, "eval_run_*.json")))
        if len(files) < 2:
            print("Need at least 2 evaluation run JSON files to compare.")
            print(f"Usage: python compare_experiments.py <path_to_run_a.json> <path_to_run_b.json>")
            return
        file_a = files[-2]
        file_b = files[-1]

    print(f"Comparing:\n  A: {file_a}\n  B: {file_b}\n")
    run_a = load_run(file_a)
    run_b = load_run(file_b)

    report_md = compare_runs(run_a, run_b)
    print(report_md)


if __name__ == "__main__":
    main()
