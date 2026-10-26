"""LangGraph state schema for the autonomous research agent."""
from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class ResearchAgentState(TypedDict):
    """Execution state container passed between LangGraph nodes."""
    task_id: str
    topic: str
    user_id: str
    constraints: List[str]
    max_tool_calls: int
    current_tool_calls: int
    retry_count: int
    max_retries: int
    require_human_approval: bool

    # Planning
    plan: Optional[Dict[str, Any]]
    subquestions: List[str]
    active_queries: List[str]

    # Tool Results & Sources
    raw_tool_results: List[Dict[str, Any]]
    collected_sources: Dict[str, Dict[str, Any]]  # Map: source_id -> SourceMetadata dict
    evidence_chunks: List[Dict[str, Any]]          # List of EvidenceChunk dicts

    # Source Validation & Approval Gate
    conflicting_evidence: List[str]
    requires_approval: bool
    approval_reason: Optional[str]
    approval_status: Optional[str]                # None, PENDING, APPROVED, REJECTED
    approval_feedback: Optional[str]

    # Report & Verification
    draft_report_markdown: Optional[str]
    verification_results: List[Dict[str, Any]]    # List of CitationVerificationResult dicts
    final_report_markdown: Optional[str]
    grounding_score: float

    # Status & Audit Trail
    status: str
    errors: List[str]
    step_history: List[Dict[str, Any]]
