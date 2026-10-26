'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { Sparkles, Sliders, ShieldAlert, ArrowRight, X } from 'lucide-react';

const SUGGESTED_TOPICS = [
  'Stateful LangGraph Checkpointing & Fault Tolerance',
  'Vector DB Indexing: HNSW vs IVFPQ Trade-offs',
  'eBPF Service Meshes vs Envoy Sidecars',
  'Speculative Decoding in Open-Source LLMs',
];

export default function TaskForm() {
  const router = useRouter();
  const [topic, setTopic] = useState('');
  const [constraintInput, setConstraintInput] = useState('');
  const [constraints, setConstraints] = useState<string[]>([]);
  const [maxToolCalls, setMaxToolCalls] = useState(12);
  const [requireApproval, setRequireApproval] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const addConstraint = () => {
    if (constraintInput.trim() && !constraints.includes(constraintInput.trim())) {
      setConstraints([...constraints, constraintInput.trim()]);
      setConstraintInput('');
    }
  };

  const removeConstraint = (tag: string) => {
    setConstraints(constraints.filter((c) => c !== tag));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const task = await api.createTask({
        topic: topic.trim(),
        constraints,
        max_tool_calls: maxToolCalls,
        require_human_approval: requireApproval,
      });
      router.push(`/tasks/${task.id}`);
    } catch (err: any) {
      setError(err.message || 'Failed to initialize research task');
      setLoading(false);
    }
  };

  return (
    <div className="bg-dark-card border border-dark-border rounded-xl p-6 shadow-xl">
      <div className="flex items-center space-x-2.5 mb-4">
        <Sparkles className="w-5 h-5 text-indigo-400" />
        <h2 className="text-lg font-semibold text-white">Initialize Autonomous Research</h2>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-950/60 border border-red-800 text-red-200 text-sm rounded-lg flex items-center space-x-2">
          <ShieldAlert className="w-4 h-4 flex-shrink-0 text-red-400" />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1.5">
            Research Topic or Technical Question
          </label>
          <textarea
            rows={3}
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="e.g. Empirical comparison of Vector Indexing HNSW vs IVFPQ at billion-scale..."
            required
            className="w-full bg-dark-bg border border-dark-border rounded-lg px-3.5 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition resize-none"
          />

          {/* Quick topic pills */}
          <div className="mt-2 flex flex-wrap gap-1.5 items-center">
            <span className="text-xs text-slate-500 mr-1">Suggestions:</span>
            {SUGGESTED_TOPICS.map((sugg) => (
              <button
                key={sugg}
                type="button"
                onClick={() => setTopic(sugg)}
                className="text-xs bg-dark-surface hover:bg-slate-700 text-slate-300 px-2.5 py-1 rounded-md border border-dark-border transition"
              >
                {sugg}
              </button>
            ))}
          </div>
        </div>

        {/* Constraints */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1.5">
            Target Constraints & Filters
          </label>
          <div className="flex space-x-2 mb-2">
            <input
              type="text"
              value={constraintInput}
              onChange={(e) => setConstraintInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  addConstraint();
                }
              }}
              placeholder="e.g. 'latency benchmarks', '2025-2026'..."
              className="flex-1 bg-dark-bg border border-dark-border rounded-lg px-3 py-1.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <button
              type="button"
              onClick={addConstraint}
              className="px-3.5 py-1.5 bg-dark-surface hover:bg-slate-700 border border-dark-border rounded-lg text-sm font-medium text-slate-200 transition"
            >
              Add
            </button>
          </div>

          <div className="flex flex-wrap gap-1.5">
            {constraints.map((c) => (
              <span
                key={c}
                className="inline-flex items-center px-2.5 py-1 rounded bg-dark-surface border border-dark-border text-xs text-indigo-300 space-x-1"
              >
                <span>{c}</span>
                <button
                  type="button"
                  onClick={() => removeConstraint(c)}
                  className="hover:text-red-400 transition"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            ))}
          </div>
        </div>

        {/* Sliders and Approval Toggle */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-dark-border/60">
          <div>
            <div className="flex justify-between items-center mb-1">
              <span className="text-xs font-medium text-slate-300 flex items-center space-x-1">
                <Sliders className="w-3.5 h-3.5 text-slate-400" />
                <span>Max Tool Calls Budget</span>
              </span>
              <span className="text-xs font-mono text-indigo-400 bg-indigo-950/60 px-2 py-0.5 rounded border border-indigo-900">
                {maxToolCalls} calls
              </span>
            </div>
            <input
              type="range"
              min={3}
              max={25}
              value={maxToolCalls}
              onChange={(e) => setMaxToolCalls(parseInt(e.target.value))}
              className="w-full accent-indigo-500 h-1.5 bg-dark-surface rounded-lg cursor-pointer"
            />
          </div>

          <div className="flex items-center justify-between sm:justify-end sm:space-x-4 bg-dark-bg/60 p-2.5 rounded-lg border border-dark-border">
            <div>
              <span className="text-xs font-medium text-slate-200 block">Require Human Review</span>
              <span className="text-[11px] text-slate-500 block">Pause in AWAITING_APPROVAL</span>
            </div>
            <input
              type="checkbox"
              checked={requireApproval}
              onChange={(e) => setRequireApproval(e.target.checked)}
              className="w-4 h-4 rounded text-indigo-600 bg-dark-surface border-dark-border focus:ring-indigo-500 cursor-pointer"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading || !topic.trim()}
          className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium text-sm rounded-lg transition shadow-md shadow-indigo-600/20 flex items-center justify-center space-x-2"
        >
          {loading ? (
            <span>Dispatching LangGraph Pipeline...</span>
          ) : (
            <>
              <span>Launch Research Workflow</span>
              <ArrowRight className="w-4 h-4" />
            </>
          )}
        </button>
      </form>
    </div>
  );
}
