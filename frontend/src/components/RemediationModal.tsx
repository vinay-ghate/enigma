import React, { useState } from 'react';
import { RemediationPlan } from '../types';
import { ShieldCheck, X, GitPullRequest, ExternalLink, Check, AlertTriangle, Loader2, FileCode } from 'lucide-react';

interface RemediationModalProps {
  plan: RemediationPlan;
  incidentId: string;
  onClose: () => void;
  onApprovalSuccess: (prUrl: string) => void;
}

export const RemediationModal: React.FC<RemediationModalProps> = ({
  plan,
  incidentId,
  onClose,
  onApprovalSuccess,
}) => {
  const [reviewer, setReviewer] = useState('oncall-judge@enigma.dev');
  const [approvalToken, setApprovalToken] = useState('APPROVE-ENIGMA-ROOTCAUSE');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [approvedPrUrl, setApprovedPrUrl] = useState<string | null>(plan.pr_url || null);
  const [error, setError] = useState<string | null>(null);

  const handleApprove = async () => {
    setIsSubmitting(true);
    setError(null);
    try {
      const res = await fetch(`/api/incidents/${incidentId}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          approval_token: approvalToken,
          reviewer,
          action: 'approve',
          notes: `Human verification completed for ${incidentId}.`,
        }),
      });

      if (!res.ok) {
        throw new Error(`Failed to approve remediation: ${res.statusText}`);
      }

      const data = await res.json();
      setApprovedPrUrl(data.pr_url);
      onApprovalSuccess(data.pr_url);
    } catch (err: any) {
      setError(err.message || 'Error approving remediation');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-[#0b1120] border border-slate-800 rounded-2xl max-w-3xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-100 flex items-center space-x-2">
                <span>Human Approval Gate — Remediation PR</span>
                <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-mono">
                  Sandbox Only
                </span>
              </h2>
              <p className="text-xs text-slate-400 font-mono">
                Target Repo: {plan.target_repo} • Branch: {plan.pr_branch}
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

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-4 text-xs">
          {approvedPrUrl ? (
            <div className="p-5 rounded-xl bg-emerald-950/30 border border-emerald-500/40 text-center space-y-3">
              <div className="w-12 h-12 rounded-full bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center mx-auto text-emerald-400">
                <Check className="w-6 h-6" />
              </div>
              <h3 className="text-sm font-bold text-emerald-300">
                Draft Pull Request Successfully Created & Logged!
              </h3>
              <p className="text-slate-300">
                Remediation has been staged to GitHub and recorded in the immutable audit trail.
              </p>
              <div className="pt-2">
                <a
                  href={approvedPrUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center space-x-2 px-4 py-2 rounded-lg bg-emerald-500 text-slate-950 font-bold hover:bg-emerald-400 transition"
                >
                  <GitPullRequest className="w-4 h-4" />
                  <span>View Draft PR on GitHub</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </div>
            </div>
          ) : (
            <>
              {/* PR Details */}
              <div className="p-3 bg-slate-900/60 rounded-xl border border-slate-800 space-y-2">
                <div className="font-mono text-slate-400 text-[11px] uppercase">
                  Pull Request Metadata
                </div>
                <div className="text-sm font-semibold text-slate-200">{plan.pr_title}</div>
                <div className="text-slate-300 whitespace-pre-line leading-relaxed font-sans bg-slate-950/80 p-3 rounded-lg border border-slate-850">
                  {plan.pr_body}
                </div>
              </div>

              {/* Commit 1: Code Revert Diff Preview */}
              <div className="space-y-1.5">
                <div className="flex items-center space-x-2 text-slate-300 font-mono font-semibold">
                  <FileCode className="w-3.5 h-3.5 text-sky-400" />
                  <span>Commit 1: Code Rollback Diff</span>
                </div>
                <pre className="bg-[#070b14] p-3 rounded-xl border border-slate-800 font-mono text-[11px] text-slate-300 overflow-x-auto max-h-48">
                  {plan.diff_preview.split('\n').map((line, idx) => {
                    let color = 'text-slate-300';
                    if (line.startsWith('+')) color = 'text-emerald-400 bg-emerald-950/20';
                    if (line.startsWith('-')) color = 'text-rose-400 bg-rose-950/20';
                    return (
                      <div key={idx} className={color}>
                        {line}
                      </div>
                    );
                  })}
                </pre>
              </div>

              {/* Commit 2: Runbook Update Patch if applicable */}
              {plan.runbook_patch && (
                <div className="space-y-1.5">
                  <div className="flex items-center space-x-2 text-amber-300 font-mono font-semibold">
                    <FileCode className="w-3.5 h-3.5 text-amber-400" />
                    <span>Commit 2: Stale Runbook Modernization Patch</span>
                  </div>
                  <pre className="bg-[#070b14] p-3 rounded-xl border border-amber-500/30 font-mono text-[11px] text-slate-300 overflow-x-auto max-h-36">
                    {plan.runbook_patch.split('\n').map((line, idx) => {
                      let color = 'text-slate-300';
                      if (line.startsWith('+')) color = 'text-emerald-400 bg-emerald-950/20';
                      if (line.startsWith('-')) color = 'text-rose-400 bg-rose-950/20';
                      return (
                        <div key={idx} className={color}>
                          {line}
                        </div>
                      );
                    })}
                  </pre>
                </div>
              )}

              {/* Reviewer inputs */}
              <div className="p-3 bg-slate-900/60 rounded-xl border border-slate-800 space-y-3">
                <div className="font-semibold text-slate-200 flex items-center space-x-1.5">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  <span>Engineering Lead Approval Token</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[10px] text-slate-400 font-mono uppercase mb-1">
                      Reviewer Email
                    </label>
                    <input
                      type="text"
                      value={reviewer}
                      onChange={(e) => setReviewer(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1.5 text-slate-200 font-mono text-xs focus:outline-none focus:border-emerald-500"
                    />
                  </div>

                  <div>
                    <label className="block text-[10px] text-slate-400 font-mono uppercase mb-1">
                      Approval Token
                    </label>
                    <input
                      type="text"
                      value={approvalToken}
                      onChange={(e) => setApprovalToken(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1.5 text-slate-200 font-mono text-xs focus:outline-none focus:border-emerald-500"
                    />
                  </div>
                </div>

                {error && (
                  <div className="p-2 rounded bg-rose-500/20 border border-rose-500/40 text-rose-300 text-xs">
                    {error}
                  </div>
                )}
              </div>
            </>
          )}
        </div>

        {/* Modal Footer */}
        {!approvedPrUrl && (
          <div className="px-6 py-3.5 border-t border-slate-800 bg-slate-900/60 flex items-center justify-between">
            <span className="text-[11px] text-slate-400 font-mono">
              Safety rule: Sandbox repo only. Zero automated production mutations.
            </span>

            <div className="flex items-center space-x-2">
              <button
                onClick={onClose}
                className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium text-xs transition"
              >
                Cancel
              </button>
              <button
                onClick={handleApprove}
                disabled={isSubmitting}
                className="px-4 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs flex items-center space-x-1.5 transition disabled:opacity-50"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Creating Sandbox PR...</span>
                  </>
                ) : (
                  <>
                    <GitPullRequest className="w-3.5 h-3.5" />
                    <span>Approve & Create Draft PR</span>
                  </>
                )}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
