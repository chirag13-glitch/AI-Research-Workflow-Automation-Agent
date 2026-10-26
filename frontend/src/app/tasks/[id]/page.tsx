'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import {
  TaskResponse,
  SourceMetadata,
  ReportResponse,
  SSEEvent,
} from '@/lib/types';
import ExecutionGraph from '@/components/ExecutionGraph';
import StreamLogViewer from '@/components/StreamLogViewer';
import ReportViewer from '@/components/ReportViewer';
import EvidenceDrawer from '@/components/EvidenceDrawer';
import ApprovalModal from '@/components/ApprovalModal';
import { ArrowLeft, Ban, AlertTriangle, RefreshCw, FileText } from 'lucide-react';
import Link from 'next/link';

export default function TaskDetailPage() {
  const params = useParams();
  const router = useRouter();
  const taskId = params.id as string;

  const [task, setTask] = useState<TaskResponse | null>(null);
  const [sources, setSources] = useState<SourceMetadata[]>([]);
  const [report, setReport] = useState<ReportResponse | null>(null);
  const [events, setEvents] = useState<SSEEvent[]>([]);
  const [isStreaming, setIsStreaming] = useState(true);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [canceling, setCanceling] = useState(false);
  const [selectedSourceId, setSelectedSourceId] = useState<string | null>(null);

  const fetchTaskData = useCallback(async () => {
    try {
      const t = await api.getTask(taskId);
      setTask(t);

      // Fetch sources
      const srcList = await api.getTaskSources(taskId);
      setSources(srcList);

      // If completed or has report, fetch report
      if (t.status === 'COMPLETED' || t.status === 'VERIFYING_REPORT') {
        try {
          const rep = await api.getTaskReport(taskId);
          setReport(rep);
        } catch {
          // Report may still be finalizing
        }
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch task');
    } finally {
      setLoading(false);
    }
  }, [taskId]);

  useEffect(() => {
    fetchTaskData();

    // Subscribe to SSE stream
    const unsubscribe = api.subscribeToTaskEvents(
      taskId,
      (ev) => {
        setEvents((prev) => [...prev, ev]);
        if (ev.status) {
          setTask((prev) => (prev ? { ...prev, status: ev.status! } : null));
          if (ev.status === 'COMPLETED' || ev.status === 'AWAITING_APPROVAL') {
            fetchTaskData();
          }
        }
      },
      () => {
        setIsStreaming(false);
      }
    );

    return () => {
      unsubscribe();
    };
  }, [taskId, fetchTaskData]);

  const handleCancel = async () => {
    if (!confirm('Are you sure you want to cancel this research task?')) return;
    setCanceling(true);
    try {
      await api.cancelTask(taskId);
      fetchTaskData();
    } catch (err: any) {
      alert(err.message || 'Failed to cancel task');
    } finally {
      setCanceling(false);
    }
  };

  if (loading) {
    return (
      <div className="py-24 text-center text-slate-500 flex flex-col items-center justify-center space-y-3">
        <RefreshCw className="w-8 h-8 animate-spin text-indigo-400" />
        <span className="text-sm">Connecting to task session...</span>
      </div>
    );
  }

  if (error || !task) {
    return (
      <div className="py-16 text-center space-y-4">
        <div className="inline-flex p-3 rounded-full bg-red-950/60 border border-red-800 text-red-400">
          <AlertTriangle className="w-8 h-8" />
        </div>
        <h2 className="text-lg font-semibold text-white">Task Unavailable</h2>
        <p className="text-sm text-slate-400 max-w-md mx-auto">{error || 'Task not found'}</p>
        <Link
          href="/"
          className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-lg bg-dark-surface border border-dark-border text-sm text-slate-200 hover:bg-slate-700 transition"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Dashboard</span>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Header & Breadcrumb */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-dark-border">
        <div>
          <Link
            href="/"
            className="inline-flex items-center space-x-1.5 text-xs text-slate-400 hover:text-slate-200 mb-2 transition"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Dashboard</span>
          </Link>
          <h1 className="text-xl sm:text-2xl font-bold text-white tracking-tight">{task.topic}</h1>
          <div className="flex items-center space-x-2 mt-1 text-xs text-slate-400 font-mono">
            <span>Task ID: {task.id}</span>
            <span>&bull;</span>
            <span>Created: {new Date(task.created_at).toLocaleString()}</span>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {task.status !== 'COMPLETED' && task.status !== 'FAILED' && task.status !== 'CANCELED' && (
            <button
              onClick={handleCancel}
              disabled={canceling}
              className="px-3 py-1.5 bg-dark-surface hover:bg-red-950/60 text-slate-300 hover:text-red-300 border border-dark-border hover:border-red-800 rounded-lg text-xs font-medium transition flex items-center space-x-1.5"
            >
              <Ban className="w-3.5 h-3.5 text-red-400" />
              <span>Cancel Task</span>
            </button>
          )}

          <button
            onClick={fetchTaskData}
            className="p-1.5 bg-dark-surface hover:bg-slate-700 text-slate-300 border border-dark-border rounded-lg text-xs transition"
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Execution Stepper */}
      <ExecutionGraph
        status={task.status}
        currentToolCalls={task.current_tool_calls}
        maxToolCalls={task.max_tool_calls}
      />

      {/* Human Approval Modal (if state is AWAITING_APPROVAL) */}
      {task.status === 'AWAITING_APPROVAL' && (
        <ApprovalModal
          taskId={task.id}
          reason={task.approval_reason}
          onResolved={fetchTaskData}
        />
      )}

      {/* Grid: Left is Stream Logs, Right is Evidence Drawer (during running phase) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        <div className={report ? 'lg:col-span-8' : 'lg:col-span-7'}>
          {report ? (
            <ReportViewer report={report} onSelectCitation={(sId) => setSelectedSourceId(sId)} />
          ) : (
            <div className="space-y-4">
              <StreamLogViewer events={events} isStreaming={isStreaming} />
              <div className="p-8 border border-dark-border rounded-xl bg-dark-card text-center text-slate-500 text-xs flex flex-col items-center justify-center space-y-2">
                <FileText className="w-8 h-8 text-slate-600 animate-pulse" />
                <span>The final report with verified citations will render here upon completion.</span>
              </div>
            </div>
          )}
        </div>

        <div className={report ? 'lg:col-span-4' : 'lg:col-span-5'}>
          <EvidenceDrawer
            sources={sources}
            citationAudit={report?.citation_audit}
            selectedSourceId={selectedSourceId}
          />
        </div>
      </div>
    </div>
  );
}
