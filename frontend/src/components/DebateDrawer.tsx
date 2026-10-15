import React from 'react';
import { AgentMessage } from '../types';
import { Bot, Sparkles, Swords, ShieldCheck, Wrench, ExternalLink, ChevronDown, ChevronUp } from 'lucide-react';

interface DebateDrawerProps {
  messages: AgentMessage[];
  isOpen: boolean;
  onToggle: () => void;
}

export const DebateDrawer: React.FC<DebateDrawerProps> = ({ messages, isOpen, onToggle }) => {
  const getAgentBadge = (agent: string, model: string) => {
    switch (agent) {
      case 'evidence':
        return {
          icon: <Bot className="w-3.5 h-3.5 text-sky-400" />,
          label: 'Evidence Agent',
          modelTag: 'Gemini 2.5 Flash',
          tagClass: 'bg-sky-500/20 text-sky-300 border-sky-500/30',
        };
      case 'hypothesis':
        return {
          icon: <Sparkles className="w-3.5 h-3.5 text-indigo-400" />,
          label: 'Hypothesis Agent',
          modelTag: 'Gemini 2.5 Pro',
          tagClass: 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30',
        };
      case 'challenger':
        return {
          icon: <Swords className="w-3.5 h-3.5 text-rose-400" />,
          label: 'Challenger Agent',
          modelTag: 'Gemini 2.5 Pro',
          tagClass: 'bg-rose-500/20 text-rose-300 border-rose-500/30',
        };
      case 'verifier':
        return {
          icon: <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />,
          label: 'Deterministic Gate',
          modelTag: 'Python Hard Checks',
          tagClass: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
        };
      case 'remediation':
        return {
          icon: <Wrench className="w-3.5 h-3.5 text-amber-400" />,
          label: 'Remediation Agent',
          modelTag: 'Gemini 2.5 Pro',
          tagClass: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
        };
      default:
        return {
          icon: <Bot className="w-3.5 h-3.5 text-slate-400" />,
          label: agent,
          modelTag: model,
          tagClass: 'bg-slate-800 text-slate-300 border-slate-700',
        };
    }
  };

  return (
    <div className="border-t border-slate-800 bg-[#090e1a] transition-all duration-300 flex flex-col">
      {/* Header bar */}
      <div
        onClick={onToggle}
        className="px-6 py-2.5 bg-slate-900/80 hover:bg-slate-900 cursor-pointer flex items-center justify-between border-b border-slate-800 select-none"
      >
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <Swords className="w-4 h-4 text-rose-400" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
              Live Adversarial Debate Stream ({messages.length} messages)
            </h3>
          </div>
          <div className="hidden sm:flex items-center space-x-2 text-[10px] font-mono text-slate-400">
            <span>Evidence (Flash)</span>
            <span>➔</span>
            <span>Hypothesis & Challenger (Pro)</span>
            <span>➔</span>
            <span>Deterministic Gate</span>
          </div>
        </div>

        <div className="flex items-center space-x-2 text-xs text-slate-400">
          <span>{isOpen ? 'Collapse Debate Drawer' : 'Expand Debate Drawer'}</span>
          {isOpen ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
        </div>
      </div>

      {/* Messages body */}
      {isOpen && (
        <div className="p-4 space-y-3 max-h-[360px] overflow-y-auto">
          {messages.length === 0 ? (
            <div className="text-center py-8 text-xs text-slate-400 font-mono">
              Waiting for agent turn-by-turn stream...
            </div>
          ) : (
            messages.map((m, idx) => {
              const meta = getAgentBadge(m.agent, m.model);
              return (
                <div
                  key={idx}
                  className="rounded-xl border border-slate-800 bg-slate-950/70 p-3.5 text-xs shadow-md space-y-2"
                >
                  {/* Message top bar */}
                  <div className="flex items-center justify-between pb-2 border-b border-slate-800/80">
                    <div className="flex items-center space-x-2">
                      <div className="p-1 rounded bg-slate-900 border border-slate-800">
                        {meta.icon}
                      </div>
                      <span className="font-bold text-slate-200">{meta.label}</span>
                      <span className="text-[10px] text-slate-400">• {m.role}</span>
                    </div>

                    <div className="flex items-center space-x-2 font-mono text-[10px]">
                      <span className={`px-2 py-0.5 rounded border ${meta.tagClass}`}>
                        {meta.modelTag}
                      </span>
                    </div>
                  </div>

                  {/* Message Markdown Content */}
                  <div className="text-slate-300 leading-relaxed whitespace-pre-line font-sans">
                    {m.content}
                  </div>

                  {/* Citations / Provenance links */}
                  {m.citations && m.citations.length > 0 && (
                    <div className="pt-2 border-t border-slate-800/80 flex flex-wrap gap-2">
                      <span className="text-[10px] text-slate-400 font-mono uppercase tracking-wider py-0.5">
                        Source Provenance:
                      </span>
                      {m.citations.map((c, cIdx) => (
                        <a
                          key={cIdx}
                          href={c.link}
                          target="_blank"
                          rel="noreferrer"
                          className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 hover:bg-slate-850 text-slate-300 border border-slate-800 hover:border-slate-700 flex items-center space-x-1"
                        >
                          <span className="truncate max-w-[160px]">{c.label}</span>
                          <ExternalLink className="w-2.5 h-2.5 text-emerald-400" />
                        </a>
                      ))}
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      )}
    </div>
  );
};
