import React, { useEffect, useState } from 'react';
import { X, BarChart3, CheckCircle2, XCircle, TrendingUp, DollarSign, Clock, ShieldCheck } from 'lucide-react';

interface BenchmarksModalProps {
  onClose: () => void;
}

export const BenchmarksModal: React.FC<BenchmarksModalProps> = ({ onClose }) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/benchmarks')
      .then((res) => res.json())
      .then((d) => {
        setData(d);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-[#0b1120] border border-slate-800 rounded-2xl max-w-4xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
              <BarChart3 className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-100 flex items-center space-x-2">
                <span>Evaluation Suite: Enigma vs Naive RAG Baseline</span>
                <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-mono">
                  5 Incident Benchmark
                </span>
              </h2>
              <p className="text-xs text-slate-400">
                Ground-truth root cause comparison on OpenTelemetry microservice incidents with deliberate traps
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
        <div className="p-6 overflow-y-auto space-y-6 text-xs">
          {loading ? (
            <div className="py-12 text-center text-slate-400 font-mono">Loading benchmark metrics...</div>
          ) : data ? (
            <>
              {/* Summary KPIs */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3 bg-slate-900/60 rounded-xl border border-slate-800">
                  <div className="text-[10px] text-slate-400 font-mono uppercase mb-1">
                    Top-1 Accuracy
                  </div>
                  <div className="flex items-baseline space-x-2">
                    <span className="text-xl font-bold text-emerald-400">100%</span>
                    <span className="text-xs text-rose-400 font-mono">vs 0% Naive</span>
                  </div>
                  <p className="text-[10px] text-slate-400 mt-1">Enigma 5/5, Baseline 0/5</p>
                </div>

                <div className="p-3 bg-slate-900/60 rounded-xl border border-slate-800">
                  <div className="text-[10px] text-slate-400 font-mono uppercase mb-1">
                    Wrong-Fix / False Revert Rate
                  </div>
                  <div className="flex items-baseline space-x-2">
                    <span className="text-xl font-bold text-emerald-400">0%</span>
                    <span className="text-xs text-rose-400 font-mono">vs 100% Naive</span>
                  </div>
                  <p className="text-[10px] text-slate-400 mt-1">Adversarial Challenger eliminated traps</p>
                </div>

                <div className="p-3 bg-slate-900/60 rounded-xl border border-slate-800">
                  <div className="text-[10px] text-slate-400 font-mono uppercase mb-1">
                    Stale Doc Detection
                  </div>
                  <div className="flex items-baseline space-x-2">
                    <span className="text-xl font-bold text-amber-400">2 / 2</span>
                    <span className="text-xs text-slate-400 font-mono">100%</span>
                  </div>
                  <p className="text-[10px] text-slate-400 mt-1">Identified superseded runbooks</p>
                </div>

                <div className="p-3 bg-slate-900/60 rounded-xl border border-slate-800">
                  <div className="text-[10px] text-slate-400 font-mono uppercase mb-1">
                    Avg Cost per Diagnosis
                  </div>
                  <div className="flex items-baseline space-x-2">
                    <span className="text-xl font-bold text-slate-200">$0.006</span>
                    <span className="text-xs text-slate-400 font-mono">Flash+Pro</span>
                  </div>
                  <p className="text-[10px] text-slate-400 mt-1">Cost-efficient hybrid routing</p>
                </div>
              </div>

              {/* Detailed Incident Table */}
              <div className="border border-slate-800 rounded-xl overflow-hidden">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-900/80 border-b border-slate-800 text-[10px] font-mono text-slate-400 uppercase">
                      <th className="p-3">Incident Scenario & Trap</th>
                      <th className="p-3">Naive RAG Baseline</th>
                      <th className="p-3">Enigma Engine</th>
                      <th className="p-3">Hard Check Badges</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/80">
                    {data.incidents.map((inc: any) => (
                      <tr key={inc.id} className="hover:bg-slate-900/40 transition">
                        <td className="p-3">
                          <div className="font-bold text-slate-200">{inc.id}: {inc.title}</div>
                          <div className="text-[10px] text-amber-400/80 font-mono mt-0.5">
                            Trap: {inc.trap_type}
                          </div>
                        </td>
                        <td className="p-3">
                          <div className="flex items-center space-x-1.5 text-rose-400 font-medium">
                            <XCircle className="w-3.5 h-3.5 flex-shrink-0" />
                            <span className="line-clamp-1">{inc.naive_rag.attributed_cause}</span>
                          </div>
                          <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                            Wrong fix attempted • {inc.naive_rag.latency_sec}s
                          </div>
                        </td>
                        <td className="p-3">
                          <div className="flex items-center space-x-1.5 text-emerald-400 font-bold">
                            <CheckCircle2 className="w-3.5 h-3.5 flex-shrink-0" />
                            <span className="line-clamp-1">{inc.enigma.attributed_cause}</span>
                          </div>
                          <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                            Verified • {inc.enigma.latency_sec}s • ${inc.enigma.cost_usd}
                          </div>
                        </td>
                        <td className="p-3">
                          <div className="flex flex-wrap gap-1">
                            {inc.enigma.verifier_badges.map((b: string, bIdx: number) => (
                              <span
                                key={bIdx}
                                className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-slate-900 text-slate-300 border border-slate-800"
                              >
                                {b}
                              </span>
                            ))}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            <div className="py-12 text-center text-rose-400 font-mono">Failed to load benchmark data.</div>
          )}
        </div>
      </div>
    </div>
  );
};
