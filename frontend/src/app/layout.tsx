import type { Metadata } from 'next';
import './globals.css';
import Link from 'next/link';
import { Layers, BarChart2, BookOpen, ShieldCheck } from 'lucide-react';
import ModeBadge from '@/components/ModeBadge';

export const metadata: Metadata = {
  title: 'AI Research & Workflow Automation Agent | SLURBUILDS',
  description: 'Bounded stateful research agent with citation verification and LangSmith tracing',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-dark-bg text-slate-100 antialiased flex flex-col">
        {/* Top Navbar */}
        <header className="border-b border-dark-border bg-dark-card/80 backdrop-blur sticky top-0 z-40">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-9 h-9 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white shadow-md shadow-indigo-500/20">
                03
              </div>
              <div>
                <span className="font-semibold text-white tracking-tight text-base sm:text-lg">
                  AI Research Agent
                </span>
                <span className="hidden sm:inline-block ml-2 px-2 py-0.5 text-xs font-medium rounded bg-indigo-950 text-indigo-400 border border-indigo-800">
                  SLURBUILDS VAULT
                </span>
              </div>
            </div>

            <nav className="flex items-center space-x-1 sm:space-x-3 text-sm font-medium">
              <Link
                href="/"
                className="px-3 py-1.5 rounded-md text-slate-300 hover:text-white hover:bg-dark-surface transition flex items-center space-x-1.5"
              >
                <Layers className="w-4 h-4 text-indigo-400" />
                <span>Research</span>
              </Link>
              <Link
                href="/evals"
                className="px-3 py-1.5 rounded-md text-slate-300 hover:text-white hover:bg-dark-surface transition flex items-center space-x-1.5"
              >
                <BarChart2 className="w-4 h-4 text-emerald-400" />
                <span>Evaluations</span>
              </Link>
              <a
                href="http://localhost:8000/docs"
                target="_blank"
                rel="noreferrer"
                className="px-3 py-1.5 rounded-md text-slate-400 hover:text-white hover:bg-dark-surface transition flex items-center space-x-1.5"
              >
                <BookOpen className="w-4 h-4" />
                <span>API</span>
              </a>
              <ModeBadge />
            </nav>
          </div>
        </header>

        {/* Main Content Container */}
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>

        {/* Minimal Footer */}
        <footer className="border-t border-dark-border py-4 text-center text-xs text-slate-500 bg-dark-card/40">
          <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between px-4">
            <p>SLURBUILDS AI VAULT &copy; 2026. Research Agent v1.0.</p>
            <div className="flex items-center space-x-2 mt-2 sm:mt-0 text-slate-400">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>SSRF Guarded &bull; Citation Verification</span>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
