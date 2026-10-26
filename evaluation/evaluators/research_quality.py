"""Research quality evaluator: calculates correctness, completeness, relevance, grounding, and citation support."""
import re
from typing import Any, Dict, List


def evaluate_research_quality(
    topic: str,
    plan: Dict[str, Any],
    report_markdown: str,
    verification_results: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Calculate deterministic research quality metrics:
    - grounding_score (0.0 - 1.0)
    - completeness_score (0.0 - 1.0)
    - relevance_score (0.0 - 1.0)
    - citation_support_ratio (0.0 - 1.0)
    - hallucination_count (integer)
    """
    if not report_markdown:
        return {
            "grounding_score": 0.0,
            "completeness_score": 0.0,
            "relevance_score": 0.0,
            "citation_support_ratio": 0.0,
            "hallucination_count": 0,
            "overall_quality_score": 0.0,
        }

    # 1. Grounding & Citation Support
    total_citations = len(verification_results)
    verified_citations = sum(1 for c in verification_results if c.get("status") == "VERIFIED")
    hallucination_count = sum(1 for c in verification_results if c.get("status") == "HALLUCINATED_ID")

    citation_support_ratio = (
        round(verified_citations / max(1, total_citations), 3) if total_citations > 0 else 1.0
    )
    # Penalty for hallucinated citation IDs
    grounding_score = max(0.0, round(citation_support_ratio - (hallucination_count * 0.2), 3))

    # 2. Completeness: check how many subquestions from plan are discussed in report
    subquestions = plan.get("subquestions", []) if plan else []
    report_lower = report_markdown.lower()
    subquestions_covered = 0

    for sq in subquestions:
        keywords = [w for w in re.findall(r"\w+", sq.lower()) if len(w) > 4]
        if any(k in report_lower for k in keywords):
            subquestions_covered += 1

    completeness_score = (
        round(subquestions_covered / max(1, len(subquestions)), 3) if subquestions else 0.8
    )

    # 3. Relevance: keyword overlap between topic and report headers
    topic_keywords = set([w for w in re.findall(r"\w+", topic.lower()) if len(w) > 3])
    report_keywords = set([w for w in re.findall(r"\w+", report_lower) if len(w) > 3])
    overlap = len(topic_keywords.intersection(report_keywords))
    relevance_score = round(overlap / max(1, len(topic_keywords)), 3) if topic_keywords else 1.0

    # 4. Composite Quality Score
    overall_quality_score = round(
        (0.45 * grounding_score) + (0.35 * completeness_score) + (0.20 * relevance_score),
        3,
    )

    return {
        "grounding_score": grounding_score,
        "completeness_score": completeness_score,
        "relevance_score": relevance_score,
        "citation_support_ratio": citation_support_ratio,
        "hallucination_count": hallucination_count,
        "overall_quality_score": overall_quality_score,
    }
