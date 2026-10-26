'use client';

import React, { useEffect, useRef } from 'react';
import { SSEEvent } from '@/lib/types';
import { Terminal, Activity } from 'lucide-react';

interface StreamLogViewerProps {
  events: SSEEvent[];
  isStreaming: boolean;
}

export default function StreamLogViewer({ events, isStreaming }: StreamLogViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [events]);

  return (
    <div className="bg-dark-card border border-dark-border rounded-xl flex flex-col h-[320px] shadow-lg">
      <div className="px-4 py-2.5 border-b border-dark-border flex items-center justify-between bg-dark-bg/40">
        <div className="flex items-center space-x-2 text-xs font-semibold text-slate-300">
          <Terminal className="w-3.5 h-3.5 text-indigo-400" />
          <span>Real-Time Agent Execution Log</span>
        </div>
        {isStreaming && (
          <div className="flex items-center space-x-1.5 text-xs text-indigo-400 font-mono">
            <span className="w-2 h-2 rounded-full bg-indigo-500 animate-ping" />
            <span>Streaming</span>
          </div>
        )}
      </div>

      <div
        ref={containerRef}
        className="flex-1 p-3 overflow-y-auto space-y-2 font-mono text-xs text-slate-300"
      >
        {events.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-slate-500 space-y-1">
            <Activity className="w-5 h-5 text-slate-600 animate-pulse" />
            <span>Awaiting pipeline dispatch events...</span>
          </div>
        ) : (
          events.map((ev, i) => (
            <div
              key={i}
              className="p-2 rounded bg-dark-bg/70 border border-dark-border/60 hover:border-slate-600 transition flex items-start space-x-2"
            >
              <span className="text-slate-500 flex-shrink-0 text-[10px] pt-0.5">
                {ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString() : '--:--:--'}
              </span>
              {ev.node && (
                <span className="px-1.5 py-0.2 rounded bg-dark-surface text-indigo-300 border border-dark-border text-[10px] font-semibold flex-shrink-0">
                  {ev.node}
                </span>
              )}
              <span className="flex-1 text-slate-200 break-words">{ev.message || JSON.stringify(ev)}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
