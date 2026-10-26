/**
 * TypeScript interfaces mirroring Backend Pydantic Schemas exactly.
 */

export type TaskStatus =
  | 'CREATED'
  | 'PLANNING'
  | 'COLLECTING_EVIDENCE'
  | 'VALIDATING_SOURCES'
  | 'AWAITING_APPROVAL'
  | 'GENERATING_REPORT'
  | 'VERIFYING_REPORT'
  | 'COMPLETED'
  | 'FAILED'
  | 'CANCELED';

export interface TaskCreate {
  topic: string;
  constraints?: string[];
  max_tool_calls?: number;
  require_human_approval?: boolean;
}

export interface TaskResponse {
  id: string;
  user_id: string;
  topic: string;
  status: TaskStatus;
  created_at: string;
  updated_at: string;
  completed_at?: string | null;
  max_tool_calls: number;
  current_tool_calls: number;
  requires_approval: boolean;
  approval_reason?: string | null;
  error_message?: string | null;
}

export interface ApprovalRequest {
  approved: boolean;
  feedback?: string | null;
}

export interface ResearchPlan {
  objectives: string[];
  subquestions: string[];
  search_queries: string[];
  information_requirements?: string[];
  expected_sections?: string[];
}

export interface SourceMetadata {
  source_id: string;
  url: string;
  title: string;
  domain: string;
  retrieved_at: string;
  status_code?: number;
  is_trusted?: boolean;
}

export type CitationStatus =
  | 'VERIFIED'
  | 'UNSUPPORTED'
  | 'HALLUCINATED_ID'
  | 'CONTRADICTED';

export interface CitationVerificationResult {
  citation_marker: string;
  source_id: string;
  url?: string | null;
  claimed_statement: string;
  supporting_excerpt?: string | null;
  status: CitationStatus;
  confidence: number;
  note?: string | null;
}

export interface ReportResponse {
  task_id: string;
  topic: string;
  content_markdown: string;
  sources: SourceMetadata[];
  citation_audit: CitationVerificationResult[];
  total_sources: number;
  total_citations: number;
  verified_citations: number;
  grounding_score: number;
}

export interface SSEEvent {
  event?: string;
  task_id?: string;
  node?: string;
  status?: TaskStatus;
  message?: string;
  timestamp?: string;
}

export interface EvaluationRunSummary {
  id: string;
  run_name: string;
  model_name: string;
  dataset_name: string;
  total_cases: number;
  passed_cases: number;
  avg_grounding_score: number;
  avg_latency_ms: number;
  created_at: string;
}

export interface EvalStatusResponse {
  online_eval_enabled: boolean;
  sample_rate: number;
  cost_cap_usd: number;
  max_cases_per_run: number;
  demo_mode: boolean;
  langsmith_tracing: boolean;
}
