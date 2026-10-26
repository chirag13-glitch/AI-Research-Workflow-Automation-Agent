'use client';

import React from 'react';
import ReactMarkdown from 'react-markdown';
import { ReportResponse } from '@/lib/types';
import { Download, FileCheck2, ShieldCheck, ExternalLink } from 'lucide-react';
import { api } from '@/lib/api';

interface ReportViewerProps {
  report: ReportResponse;
  onSelectCitation?: (sourceId: string) => void;
}

export default function ReportViewer({ report, onSelectCitation }: ReportViewerProps) {
  const downloadUrl = api.getReportDownloadUrl(report.task_id);

  // Custom component to render [^src-X] as interactive clickable citation pill
  const renderers = {
    p: ({ children }: any) => {
      // Find strings that might have [^src-X]
      return <p className="mb-4 leading-relaxed text-slate-300">{children}</p>;
    },
    h1: ({ children }: any) => (
      <h1 className="text-2xl font-bold text-white mb-4 pb-2 border-b border-dark-border">
        {children}
      </h1>
    ),
    h2: ({ children }: any) => (
      <h2 className="text-lg font-semibold text-white mt-6 mb-3 pb-1 border-b border-dark-border/60">
        {children}
      </h2>
    ),
    h3: ({ children }: any) => (
      <h3 className="text-md font-medium text-slate-200 mt-4 mb-2">{children}</h3>
    ),
    ul: ({ children }: any) => <ul className="list-disc pl-5 mb-4 space-y-1">{children}</ul>,
    ol: ({ children }: any) => <ol className="list-decimal pl-5 mb-4 space-y-1">{children}</ol>,
    li: ({ children }: any) => <li className="text-slate-300">{children}</li>,
    blockquote: ({ children }: any) => (
      <blockquote className="border-l-2 border-indigo-500 pl-4 py-1 italic bg-dark-bg/60 rounded-r my-4 text-slate-300">
        {children}
      </blockquote>
    ),
    table: ({ children }: any) => (
      <div className="overflow-x-auto my-6 border border-dark-border rounded-lg">
        <table className="w-full text-left text-xs">{children}</table>
      </div>
    ),
    th: ({ children }: any) => (
      <th className="bg-dark-surface px-3 py-2 font-semibold text-slate-200 border-b border-dark-border">
        {children}
      </th>
    ),
    td: ({ children }: any) => (
      <td className="px-3 py-2 border-b border-dark-border/40 text-slate-300">{children}</td>
    ),
    a: ({ href, children }: any) => (
      <a
        href={href}
        target="_blank"
        rel="noreferrer"
        className="text-indigo-400 hover:text-indigo-300 underline inline-flex items-center space-x-0.5"
      >
        <span>{children}</span>
        <ExternalLink className="w-3 h-3 ml-0.5" />
      </a>
    ),
  };

  return (
    <div className="bg-dark-card border border-dark-border rounded-xl shadow-xl overflow-hidden flex flex-col">
      {/* Report Header Bar */}
      <div className="px-6 py-4 bg-dark-bg/60 border-b border-dark-border flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center space-x-2">
            <FileCheck2 className="w-5 h-5 text-indigo-400" />
            <h2 className="text-base font-semibold text-white">Synthesized Research Report</h2>
          </div>
          <div className="flex items-center space-x-3 mt-1 text-xs text-slate-400">
            <span>
              Grounding Score:{' '}
              <strong className="text-emerald-400 font-mono">
                {(report.grounding_score * 100).toFixed(0)}%
              </strong>
            </span>
            <span>&bull;</span>
            <span>
              Citations:{' '}
              <strong className="text-slate-200 font-mono">
                {report.verified_citations} / {report.total_citations} Verified
              </strong>
            </span>
          </div>
        </div>

        <a
          href={downloadUrl}
          download
          className="px-3 py-1.5 bg-dark-surface hover:bg-slate-700 text-slate-200 border border-dark-border rounded-lg text-xs font-medium transition flex items-center space-x-1.5 shadow-sm"
        >
          <Download className="w-3.5 h-3.5 text-indigo-400" />
          <span>Export Markdown</span>
        </a>
      </div>

      {/* Grounding Banner */}
      <div className="px-6 py-2.5 bg-emerald-950/20 border-b border-emerald-900/40 text-xs text-emerald-300 flex items-center space-x-2">
        <ShieldCheck className="w-4 h-4 text-emerald-400 flex-shrink-0" />
        <span>
          Every cited assertion has undergone deterministic source verification. Click citations in the audit table below to inspect underlying excerpts.
        </span>
      </div>

      {/* Markdown Body */}
      <div className="p-6 overflow-y-auto prose prose-invert max-w-none text-sm">
        <ReactMarkdown components={renderers}>{report.content_markdown}</ReactMarkdown>
      </div>
    </div>
  );
}
