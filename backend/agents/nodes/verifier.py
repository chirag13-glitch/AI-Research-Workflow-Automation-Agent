"""Fact and citation verifier node: audits claims against retrieved evidence."""
from datetime import datetime
from backend.agents.state import ResearchAgentState
from backend.services.citation_verifier import verify_citations
from backend.models.schemas import TaskStatus, CitationStatus


async def verifier_node(state: ResearchAgentState) -> ResearchAgentState:
    """
    Audit draft report citations:
    - Verifies citation IDs and excerpt entailment
    - Measures grounding ratio
    - Produces final audited Markdown report
    """
    draft = state.get("draft_report_markdown") or ""
    sources = state.get("collected_sources", {})
    evidence = state.get("evidence_chunks", [])
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 2)

    try:
        results, audited_markdown, grounding = await verify_citations(draft, sources, evidence)
        serialized_results = [r.model_dump() for r in results]

        unsupported_count = sum(
            1 for r in results if r.status in (CitationStatus.UNSUPPORTED, CitationStatus.HALLUCINATED_ID)
        )

        log_entry = {
            "node": "verifier",
            "status": "COMPLETED",
            "message": f"Audited {len(results)} citations. Grounding score: {grounding:.2f}. Unsupported: {unsupported_count}",
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Check if retry is needed and allowed
        next_status = TaskStatus.COMPLETED.value
        if unsupported_count > 0 and retry_count < max_retries:
            next_status = TaskStatus.COLLECTING_EVIDENCE.value
            retry_count += 1

        return {
            **state,
            "status": next_status,
            "verification_results": serialized_results,
            "final_report_markdown": audited_markdown,
            "grounding_score": grounding,
            "retry_count": retry_count,
            "step_history": [*state.get("step_history", []), log_entry],
        }
    except Exception as e:
        error_log = {
            "node": "verifier",
            "status": "FAILED",
            "message": f"Verification error: {str(e)}",
            "timestamp": datetime.utcnow().isoformat(),
        }
        return {
            **state,
            "status": TaskStatus.COMPLETED.value,
            "final_report_markdown": draft,
            "errors": [*state.get("errors", []), str(e)],
            "step_history": [*state.get("step_history", []), error_log],
        }
