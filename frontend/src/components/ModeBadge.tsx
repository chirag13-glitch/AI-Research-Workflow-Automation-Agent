'use client';

import React, { useEffect, useState } from 'react';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function ModeBadge() {
  const [mode, setMode] = useState<string>('Demo Mode');

  useEffect(() => {
    fetch(`${API_BASE_URL}/health`)
      .then((res) => res.json())
      .then((data) => {
        if (data && data.mode) {
          setMode(data.mode);
        } else if (data && data.demo_mode === false) {
          setMode('Live Mode');
        } else {
          setMode('Demo Mode');
        }
      })
      .catch(() => {
        setMode('Demo Mode');
      });
  }, []);

  const isLive = mode === 'Live Mode';

  return (
    <span
      className={`px-2 py-0.5 text-xs font-semibold rounded-full border inline-flex items-center space-x-1.5 ${
        isLive
          ? 'bg-emerald-950/80 text-emerald-400 border-emerald-800'
          : 'bg-amber-950/80 text-amber-400 border-amber-800'
      }`}
    >
      <span
        className={`w-1.5 h-1.5 rounded-full ${isLive ? 'bg-emerald-400' : 'bg-amber-400'}`}
      />
      <span>{mode}</span>
    </span>
  );
}
