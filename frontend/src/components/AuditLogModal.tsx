import React, { useEffect, useState } from 'react';
import { X, History, ExternalLink, ShieldCheck, CheckCircle2 } from 'lucide-react';

interface AuditLogModalProps {
  onClose: () => void;
}

export const AuditLogModal: React.FC<AuditLogModalProps> = ({ onClose }) => {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/audit-log')
      .then((res) => res.json())
      .then((d) => {
        setLogs(d);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-[#0b1120] border border-slate-800 rounded-2xl max-w-2xl w-full max-h-[80vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-sky-500/10 border border-sky-500/30 text-sky-400">
              <History className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-100 flex items-center space-x-2">
                <span>Immutable Action & Approval Audit Trail</span>
              </h2>
              <p className="text-xs text-slate-400 font-mono">
                Rule #4 Compliance: Human approval required before sandbox PR creation
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 overflow-y-auto space-y-3 text-xs">
          {loading ? (
            <div className="py-12 text-center text-slate-400 font-mono">Loading audit logs...</div>
          ) : logs.length === 0 ? (
            <div className="py-12 text-center text-slate-400 font-mono">
              No remediation actions approved yet. Run an investigation and submit approval to generate audit entries.
            </div>
          ) : (
            logs.map((entry, idx) => (
              <div
                key={idx}
                className="p-3.5 bg-slate-900/60 rounded-xl border border-slate-800 space-y-2 font-mono"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    <span className="font-bold text-slate-200">{entry.action.toUpperCase()}</span>
                    <span className="text-slate-400">• {entry.incident_id}</span>
                  </div>
                  <span className="text-[10px] text-slate-400">
                    {new Date(entry.timestamp).toLocaleTimeString()}
                  </span>
                </div>

                <div className="text-[11px] text-slate-300">
                  Reviewed by: <span className="text-slate-200">{entry.reviewer}</span>
                </div>

                {entry.pr_url && (
                  <div className="pt-1.5 border-t border-slate-800/80 flex items-center justify-between">
                    <span className="text-slate-400">Target Repo: {entry.target_repo}</span>
                    <a
                      href={entry.pr_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-emerald-400 hover:text-emerald-300 flex items-center space-x-1 underline"
                    >
                      <span>Draft PR Link</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
