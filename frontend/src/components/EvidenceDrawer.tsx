'use client';

import React from 'react';
import { SourceMetadata, CitationVerificationResult } from '@/lib/types';
import { Database, ExternalLink, ShieldCheck, AlertTriangle } from 'lucide-react';

interface EvidenceDrawerProps {
  sources: SourceMetadata[];
  citationAudit?: CitationVerificationResult[];
  selectedSourceId?: string | null;
}

export default function EvidenceDrawer({
  sources,
  citationAudit = [],
  selectedSourceId,
}: EvidenceDrawerProps) {
  return (
    <div className="bg-dark-card border border-dark-border rounded-xl p-5 shadow-lg flex flex-col h-full">
      <div className="flex items-center justify-between pb-3 mb-4 border-b border-dark-border">
        <div className="flex items-center space-x-2">
          <Database className="w-4 h-4 text-indigo-400" />
          <h3 className="text-sm font-semibold text-white">Retrieved Evidence & Sources</h3>
        </div>
        <span className="text-xs font-mono text-slate-400 bg-dark-bg px-2 py-0.5 rounded border border-dark-border">
          {sources.length} sources
        </span>
      </div>

      <div className="flex-1 overflow-y-auto space-y-3 pr-1 text-xs">
        {sources.length === 0 ? (
          <div className="text-center py-8 text-slate-500">
            No external sources retrieved yet.
          </div>
        ) : (
          sources.map((src) => {
            const isSelected = selectedSourceId === src.source_id;
            // Find citations associated with this source
            const relatedCitations = citationAudit.filter((c) => c.source_id === src.source_id);

            return (
              <div
                key={src.source_id}
                className={`p-3.5 rounded-lg border transition ${
                  isSelected
                    ? 'bg-indigo-950/40 border-indigo-500 ring-1 ring-indigo-500'
                    : 'bg-dark-bg/80 border-dark-border hover:border-slate-600'
                }`}
              >
                <div className="flex items-start justify-between gap-2 mb-1">
                  <div className="flex items-center space-x-1.5">
                    <span className="font-mono font-bold text-indigo-400 bg-indigo-950/80 px-1.5 py-0.5 rounded border border-indigo-900 text-[11px]">
                      {src.source_id}
                    </span>
                    <span className="text-slate-400 font-mono text-[11px] truncate max-w-[140px]">
                      {src.domain}
                    </span>
                  </div>

                  {src.is_trusted !== false ? (
                    <span className="text-[10px] text-emerald-400 flex items-center space-x-0.5">
                      <ShieldCheck className="w-3 h-3 text-emerald-400" />
                      <span>Verified</span>
                    </span>
                  ) : (
                    <span className="text-[10px] text-amber-400 flex items-center space-x-0.5">
                      <AlertTriangle className="w-3 h-3 text-amber-400" />
                      <span>Sanitized</span>
                    </span>
                  )}
                </div>

                <h4 className="text-slate-200 font-medium line-clamp-2 mb-2">{src.title}</h4>

                {relatedCitations.length > 0 && relatedCitations[0].supporting_excerpt && (
                  <div className="bg-dark-surface/60 p-2 rounded border border-dark-border/60 text-slate-300 italic mb-2 text-[11px] leading-relaxed">
                    "{relatedCitations[0].supporting_excerpt}"
                  </div>
                )}

                <div className="flex items-center justify-between pt-1 border-t border-dark-border/40 text-[10px] text-slate-500">
                  <span>{new Date(src.retrieved_at).toLocaleTimeString()}</span>
                  <a
                    href={src.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-indigo-400 hover:text-indigo-300 flex items-center space-x-0.5"
                  >
                    <span>Visit Source</span>
                    <ExternalLink className="w-2.5 h-2.5 ml-0.5" />
                  </a>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
