'use client';

import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { api } from '@/lib/api';
import { Scale, ArrowRight, Loader2 } from 'lucide-react';

interface EvalComparisonProps {
  availableRuns: { id: string; label: string }[];
}

export default function EvalComparison({ availableRuns }: EvalComparisonProps) {
  const [runA, setRunA] = useState(availableRuns[0]?.id || '');
  const [runB, setRunB] = useState(availableRuns[1]?.id || availableRuns[0]?.id || '');
  const [comparisonMd, setComparisonMd] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCompare = async () => {
    if (!runA || !runB) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.compareRuns(runA, runB);
      setComparisonMd(res.markdown_comparison);
    } catch (err: any) {
      setError(err.message || 'Comparison failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-dark-card border border-dark-border rounded-xl p-6 shadow-xl">
      <div className="flex items-center space-x-2.5 mb-4">
        <Scale className="w-5 h-5 text-emerald-400" />
        <h3 className="text-base font-semibold text-white">Compare Evaluation Experiments</h3>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">Baseline Run (A)</label>
          <select
            value={runA}
            onChange={(e) => setRunA(e.target.value)}
            className="w-full bg-dark-bg border border-dark-border rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            {availableRuns.map((r) => (
              <option key={r.id} value={r.id}>
                {r.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">Candidate Run (B)</label>
          <select
            value={runB}
            onChange={(e) => setRunB(e.target.value)}
            className="w-full bg-dark-bg border border-dark-border rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            {availableRuns.map((r) => (
              <option key={r.id} value={r.id}>
                {r.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <button
        type="button"
        onClick={handleCompare}
        disabled={loading || !runA || !runB}
        className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-medium text-xs rounded-lg transition flex items-center space-x-2"
      >
        {loading ? (
          <>
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            <span>Computing Real Deltas...</span>
          </>
        ) : (
          <>
            <span>Compute Experiment Deltas</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </>
        )}
      </button>

      {error && <div className="mt-4 p-3 bg-red-950/50 text-red-300 text-xs rounded-lg">{error}</div>}

      {comparisonMd && (
        <div className="mt-6 p-5 bg-dark-bg/80 border border-dark-border rounded-xl prose prose-invert max-w-none text-xs">
          <ReactMarkdown>{comparisonMd}</ReactMarkdown>
        </div>
      )}
    </div>
  );
}
