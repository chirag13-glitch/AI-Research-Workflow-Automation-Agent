'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import TaskForm from '@/components/TaskForm';
import { api } from '@/lib/api';
import { TaskResponse } from '@/lib/types';
import { Clock, CheckCircle2, AlertCircle, ArrowUpRight, RefreshCw, Activity } from 'lucide-react';

export default function DashboardPage() {
  const [tasks, setTasks] = useState<TaskResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTasks = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.listTasks();
      setTasks(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch task history');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, []);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return (
          <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800">
            COMPLETED
          </span>
        );
      case 'AWAITING_APPROVAL':
        return (
          <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-950 text-amber-400 border border-amber-800 animate-pulse">
            APPROVAL NEEDED
          </span>
        );
      case 'FAILED':
        return (
          <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-red-950 text-red-400 border border-red-800">
            FAILED
          </span>
        );
      case 'CANCELED':
        return (
          <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-800 text-slate-400 border border-slate-700">
            CANCELED
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-indigo-950 text-indigo-400 border border-indigo-800 animate-pulse">
            {status}
          </span>
        );
    }
  };

  return (
    <div className="space-y-8">
      {/* Top Hero Banner */}
      <div className="bg-gradient-to-r from-dark-card via-dark-card to-indigo-950/40 border border-dark-border rounded-2xl p-6 sm:p-8 shadow-xl">
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
          Autonomous Research & Citation Verification Engine
        </h1>
        <p className="mt-2 text-sm sm:text-base text-slate-400 max-w-3xl leading-relaxed">
          Bounded stateful agent powered by LangGraph, SSRF-guarded tool allowlists, and Citation Verification. Every citation is grounded in verifiable external source excerpts.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Task Creator Form */}
        <div className="lg:col-span-5">
          <TaskForm />
        </div>

        {/* Right Column: Execution History */}
        <div className="lg:col-span-7">
          <div className="bg-dark-card border border-dark-border rounded-xl shadow-xl overflow-hidden flex flex-col">
            <div className="p-5 border-b border-dark-border flex items-center justify-between bg-dark-bg/40">
              <div className="flex items-center space-x-2">
                <Clock className="w-4 h-4 text-indigo-400" />
                <h3 className="text-base font-semibold text-white">Recent Research Tasks</h3>
              </div>
              <button
                onClick={fetchTasks}
                className="p-1.5 rounded-lg bg-dark-surface hover:bg-slate-700 text-slate-400 hover:text-white transition"
                title="Refresh history"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
            </div>

            {error && (
              <div className="m-4 p-3 bg-red-950/60 border border-red-800 text-red-200 text-xs rounded-lg flex items-center space-x-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0 text-red-400" />
                <span>{error}</span>
              </div>
            )}

            <div className="divide-y divide-dark-border/60 overflow-y-auto max-h-[540px]">
              {loading ? (
                <div className="py-12 flex flex-col items-center justify-center text-slate-500 space-y-2">
                  <Activity className="w-6 h-6 text-indigo-400 animate-spin" />
                  <span className="text-xs">Loading research history...</span>
                </div>
              ) : tasks.length === 0 ? (
                <div className="py-12 text-center text-slate-500 text-xs">
                  No research tasks found. Submit a topic to start your first bounded run.
                </div>
              ) : (
                tasks.map((task) => (
                  <Link
                    key={task.id}
                    href={`/tasks/${task.id}`}
                    className="p-4 hover:bg-dark-surface/50 transition flex items-center justify-between group block"
                  >
                    <div className="pr-4 space-y-1.5 flex-1 min-w-0">
                      <div className="flex items-center space-x-2">
                        {getStatusBadge(task.status)}
                        <span className="text-[11px] font-mono text-slate-500">{task.id}</span>
                      </div>
                      <h4 className="text-sm font-medium text-slate-200 truncate group-hover:text-indigo-300 transition">
                        {task.topic}
                      </h4>
                      <div className="flex items-center space-x-3 text-[11px] text-slate-500">
                        <span>{new Date(task.created_at).toLocaleString()}</span>
                        <span>&bull;</span>
                        <span>{task.current_tool_calls} / {task.max_tool_calls} tools used</span>
                      </div>
                    </div>
                    <ArrowUpRight className="w-4 h-4 text-slate-500 group-hover:text-indigo-400 transition flex-shrink-0" />
                  </Link>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
