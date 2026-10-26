'use client';

import React, { useState } from 'react';
import { api } from '@/lib/api';
import { PauseCircle, CheckCircle, XCircle, AlertCircle } from 'lucide-react';

interface ApprovalModalProps {
  taskId: string;
  reason?: string | null;
  onResolved: () => void;
}

export default function ApprovalModal({ taskId, reason, onResolved }: ApprovalModalProps) {
  const [feedback, setFeedback] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAction = async (approved: boolean) => {
    setSubmitting(true);
    setError(null);
    try {
      await api.approveTask(taskId, { approved, feedback: feedback.trim() || null });
      onResolved();
    } catch (err: any) {
      setError(err.message || 'Failed to submit approval decision');
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in">
      <div className="bg-dark-card border border-amber-600/60 rounded-xl max-w-lg w-full p-6 shadow-2xl relative">
        <div className="flex items-center space-x-3 mb-4">
          <div className="w-10 h-10 rounded-full bg-amber-950/80 border border-amber-600 flex items-center justify-center text-amber-400">
            <PauseCircle className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Human Approval Required</h3>
            <span className="text-xs text-amber-400 font-medium">Task Paused at Approval Gate</span>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-950/60 border border-red-800 text-red-200 text-xs rounded-lg flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0 text-red-400" />
            <span>{error}</span>
          </div>
        )}

        <div className="bg-dark-bg p-3.5 rounded-lg border border-dark-border mb-4 text-xs text-slate-300">
          <span className="font-semibold text-slate-200 block mb-1">Reason for Pause:</span>
          <p>{reason || 'Agent encountered ambiguity or reached user-defined checkpoint before synthesis.'}</p>
        </div>

        <div className="mb-5">
          <label className="block text-xs font-medium text-slate-300 mb-1.5">
            Refinement Feedback or Guidance (Optional)
          </label>
          <textarea
            rows={2}
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="e.g. 'Focus primarily on latency benchmarks in the final section'..."
            className="w-full bg-dark-bg border border-dark-border rounded-lg px-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
          />
        </div>

        <div className="flex items-center justify-end space-x-3">
          <button
            type="button"
            disabled={submitting}
            onClick={() => handleAction(false)}
            className="px-4 py-2 bg-dark-surface hover:bg-slate-700 text-slate-300 border border-dark-border rounded-lg text-xs font-medium transition flex items-center space-x-1.5 disabled:opacity-50"
          >
            <XCircle className="w-4 h-4 text-red-400" />
            <span>Reject & Cancel</span>
          </button>

          <button
            type="button"
            disabled={submitting}
            onClick={() => handleAction(true)}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold transition flex items-center space-x-1.5 shadow-md shadow-indigo-600/20 disabled:opacity-50"
          >
            <CheckCircle className="w-4 h-4" />
            <span>Approve & Resume Pipeline</span>
          </button>
        </div>
      </div>
    </div>
  );
}
