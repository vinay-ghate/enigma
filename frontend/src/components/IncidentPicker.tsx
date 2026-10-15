import React from 'react';
import { Incident } from '../types';
import { AlertCircle, Flame, Zap, ShieldAlert, Clock, ArrowRight, Loader2 } from 'lucide-react';

interface IncidentPickerProps {
  incidents: Incident[];
  selectedIncidentId: string;
  onSelectIncident: (id: string) => void;
  onRunInvestigation: (id: string) => void;
  isRunning: boolean;
}

export const IncidentPicker: React.FC<IncidentPickerProps> = ({
  incidents,
  selectedIncidentId,
  onSelectIncident,
  onRunInvestigation,
  isRunning,
}) => {
  return (
    <div className="bg-[#0b1120] border-b border-slate-800/80 px-6 py-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <Flame className="w-4 h-4 text-rose-400" />
          <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">
            Incident Scenarios (3 Hero + 2 Benchmark)
          </h2>
        </div>
        <span className="text-xs text-slate-400">
          Select a production alert scenario to launch adversarial root-cause investigation
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-3">
        {incidents.map((inc) => {
          const isSelected = inc.id === selectedIncidentId;
          const isCrit = inc.severity === 'critical';

          return (
            <div
              key={inc.id}
              onClick={() => onSelectIncident(inc.id)}
              className={`cursor-pointer rounded-xl p-3.5 border transition relative flex flex-col justify-between ${
                isSelected
                  ? 'bg-slate-900 border-emerald-500/60 shadow-lg shadow-emerald-950/40 ring-1 ring-emerald-500/30'
                  : 'bg-slate-950/60 border-slate-800/80 hover:border-slate-700 hover:bg-slate-900/40'
              }`}
            >
              {/* Top row */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-1.5">
                    <span
                      className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded ${
                        isCrit
                          ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                          : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                      }`}
                    >
                      {inc.id}
                    </span>
                    {inc.is_hero && (
                      <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/20">
                        HERO
                      </span>
                    )}
                  </div>
                  <span className="text-[11px] font-mono text-slate-400 flex items-center">
                    <Clock className="w-3 h-3 mr-1 text-slate-400" />
                    {inc.service_id.replace('svc-', '')}
                  </span>
                </div>

                <h3 className="text-xs font-semibold text-slate-200 line-clamp-2 leading-snug mb-1.5">
                  {inc.title}
                </h3>
                <p className="text-[11px] text-slate-400 line-clamp-2 mb-3">
                  {inc.description}
                </p>
              </div>

              {/* Bottom row */}
              <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between">
                <span className="text-[10px] text-slate-400 font-mono truncate max-w-[110px]" title={inc.trap_type}>
                  {inc.trap_type.replace(/_/g, ' ')}
                </span>

                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onSelectIncident(inc.id);
                    onRunInvestigation(inc.id);
                  }}
                  disabled={isRunning}
                  className={`text-[11px] px-2.5 py-1 rounded-md font-semibold flex items-center space-x-1 transition ${
                    isSelected
                      ? 'bg-emerald-500 text-slate-950 hover:bg-emerald-400'
                      : 'bg-slate-800 text-slate-200 hover:bg-slate-700'
                  }`}
                >
                  {isRunning && isSelected ? (
                    <>
                      <Loader2 className="w-3 h-3 animate-spin" />
                      <span>Running</span>
                    </>
                  ) : (
                    <>
                      <span>Investigate</span>
                      <ArrowRight className="w-3 h-3" />
                    </>
                  )}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
