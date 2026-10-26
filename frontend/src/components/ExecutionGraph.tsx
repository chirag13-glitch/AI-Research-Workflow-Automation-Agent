'use client';

import React from 'react';
import { TaskStatus } from '@/lib/types';
import {
  FileText,
  Search,
  DownloadCloud,
  CheckCircle2,
  Clock,
  AlertCircle,
  FileCheck,
  PauseCircle,
} from 'lucide-react';

interface ExecutionGraphProps {
  status: TaskStatus;
  currentToolCalls: number;
  maxToolCalls: number;
}

const GRAPH_NODES = [
  { id: 'PLANNING', label: 'Planner', icon: FileText },
  { id: 'COLLECTING_EVIDENCE', label: 'Search & Fetch', icon: Search },
  { id: 'VALIDATING_SOURCES', label: 'Validation', icon: CheckCircle2 },
  { id: 'AWAITING_APPROVAL', label: 'Approval Gate', icon: PauseCircle },
  { id: 'GENERATING_REPORT', label: 'Synthesis', icon: FileText },
  { id: 'VERIFYING_REPORT', label: 'Citation Audit', icon: FileCheck },
  { id: 'COMPLETED', label: 'Completed', icon: CheckCircle2 },
];

export default function ExecutionGraph({
  status,
  currentToolCalls,
  maxToolCalls,
}: ExecutionGraphProps) {
  const getStatusIndex = (st: TaskStatus) => {
    switch (st) {
      case 'CREATED':
        return -1;
      case 'PLANNING':
        return 0;
      case 'COLLECTING_EVIDENCE':
        return 1;
      case 'VALIDATING_SOURCES':
        return 2;
      case 'AWAITING_APPROVAL':
        return 3;
      case 'GENERATING_REPORT':
        return 4;
      case 'VERIFYING_REPORT':
        return 5;
      case 'COMPLETED':
        return 6;
      case 'FAILED':
      case 'CANCELED':
        return 99;
      default:
        return 0;
    }
  };

  const currentIndex = getStatusIndex(status);

  return (
    <div className="bg-dark-card border border-dark-border rounded-xl p-5 shadow-lg">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 mb-4 border-b border-dark-border gap-2">
        <div className="flex items-center space-x-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            LangGraph Execution State
          </span>
          <span
            className={`px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider ${
              status === 'COMPLETED'
                ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-800'
                : status === 'AWAITING_APPROVAL'
                ? 'bg-amber-950/80 text-amber-400 border border-amber-800 animate-pulse'
                : status === 'FAILED'
                ? 'bg-red-950/80 text-red-400 border border-red-800'
                : status === 'CANCELED'
                ? 'bg-slate-800 text-slate-400 border border-slate-700'
                : 'bg-indigo-950/80 text-indigo-400 border border-indigo-800 animate-pulse'
            }`}
          >
            {status}
          </span>
        </div>

        <div className="text-xs text-slate-400 font-mono">
          Tool Budget: <span className="text-indigo-400 font-semibold">{currentToolCalls}</span> / {maxToolCalls} calls
        </div>
      </div>

      {/* Stepper Timeline */}
      <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-7 gap-2">
        {GRAPH_NODES.map((node, idx) => {
          const Icon = node.icon;
          const isPassed = currentIndex > idx && status !== 'FAILED';
          const isCurrent = currentIndex === idx;
          const isWaiting = node.id === 'AWAITING_APPROVAL' && status === 'AWAITING_APPROVAL';

          let stateStyle = 'bg-dark-bg border-dark-border text-slate-500';
          if (isPassed) {
            stateStyle = 'bg-emerald-950/30 border-emerald-800/80 text-emerald-400';
          } else if (isWaiting) {
            stateStyle = 'bg-amber-950/40 border-amber-600 text-amber-300 ring-2 ring-amber-500/20';
          } else if (isCurrent) {
            stateStyle = 'bg-indigo-950/40 border-indigo-600 text-indigo-300 ring-2 ring-indigo-500/20';
          }

          return (
            <div
              key={node.id}
              className={`p-3 rounded-lg border flex flex-col items-center justify-center text-center transition ${stateStyle}`}
            >
              <div className="mb-1.5">
                {isPassed ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : isCurrent ? (
                  <Icon className="w-4 h-4 text-indigo-400 animate-bounce" />
                ) : (
                  <Icon className="w-4 h-4" />
                )}
              </div>
              <span className="text-[11px] font-medium leading-tight">{node.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
