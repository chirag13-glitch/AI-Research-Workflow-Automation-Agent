"""Report generator node: synthesizes collected evidence into structured Markdown report."""
from datetime import datetime
from backend.agents.state import ResearchAgentState
from backend.services.llm_adapter import llm_adapter
from backend.models.schemas import ResearchPlan, SourceMetadata, EvidenceChunk, TaskStatus


async def report_generator_node(state: ResearchAgentState) -> ResearchAgentState:
    """
    Synthesize research report:
    - Incorporate objectives and expected sections from plan
    - Cite evidence using explicit [^src-X] references
    - Produce draft Markdown
    """
    topic = state.get("topic", "")
    plan_dict = state.get("plan") or {}
    sources_dict = state.get("collected_sources", {})
    evidence_list = state.get("evidence_chunks", [])

    # Reconstruct pydantic models for adapter
    plan = ResearchPlan(
        objectives=plan_dict.get("objectives", [f"Research on {topic}"]),
        subquestions=plan_dict.get("subquestions", [f"What is {topic}?"]),
        search_queries=plan_dict.get("search_queries", [topic]),
        information_requirements=plan_dict.get("information_requirements", []),
        expected_sections=plan_dict.get("expected_sections", ["Summary", "Analysis", "Conclusion"]),
    )

    sources = [
        SourceMetadata(
            source_id=s["source_id"],
            url=s["url"],
            title=s.get("title", "Untitled"),
            domain=s.get("domain", ""),
        )
        for s in sources_dict.values()
    ]

    evidence = [
        EvidenceChunk(
            chunk_id=e["chunk_id"],
            source_id=e["source_id"],
            url=e["url"],
            text=e["text"],
            char_count=e["char_count"],
        )
        for e in evidence_list
    ]

    try:
        draft_markdown = await llm_adapter.generate_report(topic, plan, evidence, sources)
        log_entry = {
            "node": "report_generator",
            "status": "COMPLETED",
            "message": f"Synthesized report draft ({len(draft_markdown)} characters).",
            "timestamp": datetime.utcnow().isoformat(),
        }
        return {
            **state,
            "status": TaskStatus.GENERATING_REPORT.value,
            "draft_report_markdown": draft_markdown,
            "step_history": [*state.get("step_history", []), log_entry],
        }
    except Exception as e:
        error_log = {
            "node": "report_generator",
            "status": "FAILED",
            "message": f"Report generation failed: {str(e)}",
            "timestamp": datetime.utcnow().isoformat(),
        }
        return {
            **state,
            "errors": [*state.get("errors", []), str(e)],
            "step_history": [*state.get("step_history", []), error_log],
        }
