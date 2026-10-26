import {
  TaskCreate,
  TaskResponse,
  ApprovalRequest,
  SourceMetadata,
  ReportResponse,
  SSEEvent,
  EvaluationRunSummary,
  EvalStatusResponse,
} from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || '';

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const headers = new Headers(options.headers || {});
  headers.set('Content-Type', 'application/json');

  if (API_KEY) {
    headers.set('Authorization', `Bearer ${API_KEY}`);
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = `HTTP ${response.status}: ${response.statusText}`;
    try {
      const errorJson = await response.json();
      if (errorJson && errorJson.detail) {
        errorDetail = errorJson.detail;
      }
    } catch {
      // Use fallback errorDetail
    }
    throw new ApiError(errorDetail, response.status);
  }

  return response.json();
}

export const api = {
  // Tasks
  async createTask(data: TaskCreate): Promise<TaskResponse> {
    return request<TaskResponse>('/api/v1/research/tasks', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async listTasks(): Promise<TaskResponse[]> {
    return request<TaskResponse[]>('/api/v1/research/tasks');
  },

  async getTask(taskId: string): Promise<TaskResponse> {
    return request<TaskResponse>(`/api/v1/research/tasks/${taskId}`);
  },

  async getTaskSources(taskId: string): Promise<SourceMetadata[]> {
    return request<SourceMetadata[]>(`/api/v1/research/tasks/${taskId}/sources`);
  },

  async getTaskReport(taskId: string): Promise<ReportResponse> {
    return request<ReportResponse>(`/api/v1/research/tasks/${taskId}/report`);
  },

  getReportDownloadUrl(taskId: string): string {
    return `${API_BASE_URL}/api/v1/research/tasks/${taskId}/report/download`;
  },

  async approveTask(taskId: string, approval: ApprovalRequest): Promise<{ message: string; approved: boolean }> {
    return request<{ message: string; approved: boolean }>(`/api/v1/research/tasks/${taskId}/approve`, {
      method: 'POST',
      body: JSON.stringify(approval),
    });
  },

  async cancelTask(taskId: string): Promise<{ message: string }> {
    return request<{ message: string }>(`/api/v1/research/tasks/${taskId}/cancel`, {
      method: 'POST',
    });
  },

  // Evaluations
  async getEvalStatus(): Promise<EvalStatusResponse> {
    return request<EvalStatusResponse>('/api/v1/evaluations/status');
  },

  async listEvalRuns(): Promise<{ database_runs: EvaluationRunSummary[]; file_runs: any[] }> {
    return request<{ database_runs: EvaluationRunSummary[]; file_runs: any[] }>('/api/v1/evaluations/runs');
  },

  async triggerEvalRun(maxCases: number = 10): Promise<{ message: string; run_id: string }> {
    return request<{ message: string; run_id: string }>('/api/v1/evaluations/runs', {
      method: 'POST',
      body: JSON.stringify({ max_cases: maxCases, run_name: 'Dashboard Benchmark Run' }),
    });
  },

  async compareRuns(runA: string, runB: string): Promise<{ run_a: string; run_b: string; markdown_comparison: string }> {
    const params = new URLSearchParams({ run_a_id: runA, run_b_id: runB });
    return request<{ run_a: string; run_b: string; markdown_comparison: string }>(`/api/v1/evaluations/compare?${params.toString()}`);
  },

  // Real-time Server-Sent Events (SSE) subscriber
  subscribeToTaskEvents(
    taskId: string,
    onEvent: (event: SSEEvent) => void,
    onError?: (err: any) => void
  ): () => void {
    const url = `${API_BASE_URL}/api/v1/research/tasks/${taskId}/events`;
    const eventSource = new EventSource(url);

    eventSource.onmessage = (e) => {
      try {
        const parsed: SSEEvent = JSON.parse(e.data);
        onEvent(parsed);
      } catch (err) {
        console.error('Failed to parse SSE payload', err);
      }
    };

    eventSource.onerror = (err) => {
      if (onError) onError(err);
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  },
};
