import React from 'react';
import { ShieldCheck, Play, RotateCcw, BarChart3, History, GitFork } from 'lucide-react';

interface HeaderProps {
  mode: 'live' | 'replay';
  onModeToggle: (newMode: 'live' | 'replay') => void;
  onOpenBenchmarks: () => void;
  onOpenAuditLog: () => void;
  isRunning: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  mode,
  onModeToggle,
  onOpenBenchmarks,
  onOpenAuditLog,
  isRunning,
}) => {
  return (
    <header className="border-b border-slate-800 bg-[#090e1a]/90 backdrop-blur-md sticky top-0 z-40 px-6 py-3.5 flex items-center justify-between">
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center">
            <span className="text-emerald-400 font-bold text-lg font-mono">Σ</span>
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-lg font-bold text-slate-100 tracking-tight">ENIGMA</h1>
              <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                Causal Engine v0.2
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Google ADK Multi-Agent Incident Root-Cause Investigation & Deterministic Gate
            </p>
          </div>
        </div>

        <div className="hidden lg:flex items-center space-x-2 pl-4 border-l border-slate-800 text-xs">
          <a
            href="https://github.com/enigma-sandbox/opentelemetry-demo"
            target="_blank"
            rel="noreferrer"
            className="flex items-center space-x-1.5 px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700 transition"
          >
            <GitFork className="w-3.5 h-3.5 text-slate-400" />
            <span className="font-mono">enigma-sandbox/opentelemetry-demo</span>
          </a>
        </div>
      </div>

      <div className="flex items-center space-x-3">
        {/* Judge Invite Tag */}
        <div className="hidden md:flex items-center space-x-1.5 px-3 py-1 bg-amber-500/10 border border-amber-500/20 rounded text-xs text-amber-300 font-mono">
          <ShieldCheck className="w-3.5 h-3.5 text-amber-400" />
          <span>JUDGE: ENIGMA-GCP-2026</span>
        </div>

        {/* Live vs Replay Toggle */}
        <div className="flex items-center bg-slate-900 border border-slate-800 rounded-lg p-1 text-xs">
          <button
            onClick={() => onModeToggle('live')}
            disabled={isRunning}
            className={`flex items-center space-x-1 px-3 py-1 rounded-md transition ${
              mode === 'live'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-semibold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Play className="w-3 h-3" />
            <span>Live ADK</span>
          </button>
          <button
            onClick={() => onModeToggle('replay')}
            disabled={isRunning}
            className={`flex items-center space-x-1 px-3 py-1 rounded-md transition ${
              mode === 'replay'
                ? 'bg-sky-500/20 text-sky-300 border border-sky-500/40 font-semibold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <RotateCcw className="w-3 h-3" />
            <span>Cached Replay</span>
          </button>
        </div>

        {/* Benchmarks Button */}
        <button
          onClick={onOpenBenchmarks}
          className="flex items-center space-x-1.5 px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-300 hover:border-slate-700 hover:text-white transition font-medium"
        >
          <BarChart3 className="w-3.5 h-3.5 text-emerald-400" />
          <span>Benchmarks (5/5)</span>
        </button>

        {/* Audit Log Button */}
        <button
          onClick={onOpenAuditLog}
          className="flex items-center space-x-1.5 px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-300 hover:border-slate-700 hover:text-white transition font-medium"
        >
          <History className="w-3.5 h-3.5 text-sky-400" />
          <span>Audit Log</span>
        </button>
      </div>
    </header>
  );
};
