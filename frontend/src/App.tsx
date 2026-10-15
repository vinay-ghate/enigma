import React, { useState, useEffect, useRef } from 'react';
import { Header } from './components/Header';
import { IncidentPicker } from './components/IncidentPicker';
import { CompareView } from './components/CompareView';
import { CausalGraph } from './components/CausalGraph';
import { DebateDrawer } from './components/DebateDrawer';
import { RemediationModal } from './components/RemediationModal';
import { BenchmarksModal } from './components/BenchmarksModal';
import { AuditLogModal } from './components/AuditLogModal';
import {
  Incident,
  AgentMessage,
  NaiveRAGResult,
  VerificationBadges,
  RemediationPlan,
  InvestigationMetrics,
} from './types';
import { Node, Edge } from '@xyflow/react';
import { AlertCircle, Activity, Sparkles, DollarSign, Clock, ShieldCheck } from 'lucide-react';

export const App: React.FC = () => {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [selectedIncidentId, setSelectedIncidentId] = useState<string>('INC-101');
  const [mode, setMode] = useState<'live' | 'replay'>('live');

  // Investigation state
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [agentMessages, setAgentMessages] = useState<AgentMessage[]>([]);
  const [naiveRag, setNaiveRag] = useState<NaiveRAGResult | null>(null);
  const [graphNodes, setGraphNodes] = useState<Node[]>([]);
  const [graphEdges, setGraphEdges] = useState<Edge[]>([]);
  const [chosenCauseId, setChosenCauseId] = useState<string | null>(null);
  const [verificationBadges, setVerificationBadges] = useState<VerificationBadges | null>(null);
  const [remediationPlan, setRemediationPlan] = useState<RemediationPlan | null>(null);
  const [metrics, setMetrics] = useState<InvestigationMetrics | null>(null);

  // Modals & Drawers
  const [isDebateOpen, setIsDebateOpen] = useState<boolean>(true);
  const [isRemediationOpen, setIsRemediationOpen] = useState<boolean>(false);
  const [isBenchmarksOpen, setIsBenchmarksOpen] = useState<boolean>(false);
  const [isAuditLogOpen, setIsAuditLogOpen] = useState<boolean>(false);

  // Active SSE source
  const sseRef = useRef<EventSource | null>(null);

  // Load incidents on mount
  useEffect(() => {
    fetch('/api/incidents')
      .then((res) => res.json())
      .then((data: Incident[]) => {
        setIncidents(data);
        if (data.length > 0) {
          setSelectedIncidentId(data[0].id);
          // Initial graph load
          loadStaticGraph(data[0].id);
        }
      })
      .catch((err) => console.error('Failed to load incidents', err));
  }, []);

  const loadStaticGraph = (id: string) => {
    fetch(`/api/incidents/${id}/graph`)
      .then((res) => res.json())
      .then((data) => {
        setGraphNodes(data.nodes || []);
        setGraphEdges(data.edges || []);
      })
      .catch((err) => console.error('Failed to load static graph', err));
  };

  const handleSelectIncident = (id: string) => {
    setSelectedIncidentId(id);
    resetInvestigationState();
    loadStaticGraph(id);
  };

  const resetInvestigationState = () => {
    if (sseRef.current) {
      sseRef.current.close();
      sseRef.current = null;
    }
    setAgentMessages([]);
    setNaiveRag(null);
    setChosenCauseId(null);
    setVerificationBadges(null);
    setRemediationPlan(null);
    setMetrics(null);
    setIsRunning(false);
  };

  const runInvestigation = (incidentId: string) => {
    resetInvestigationState();
    setIsRunning(true);
    setIsDebateOpen(true);

    const sse = new EventSource(`/api/incidents/${incidentId}/investigate?mode=${mode}`);
    sseRef.current = sse;

    sse.addEventListener('timeline_ready', (e: MessageEvent) => {
      const data = JSON.parse(e.data);
      console.log('Timeline ready:', data);
    });

    sse.addEventListener('naive_rag_ready', (e: MessageEvent) => {
      const data = JSON.parse(e.data);
      setNaiveRag(data);
    });

    sse.addEventListener('agent_message', (e: MessageEvent) => {
      const msg: AgentMessage = JSON.parse(e.data);
      setAgentMessages((prev) => [...prev, msg]);
    });

    sse.addEventListener('graph_updated', (e: MessageEvent) => {
      const data = JSON.parse(e.data);
      if (data.nodes) setGraphNodes(data.nodes);
      if (data.edges) setGraphEdges(data.edges);
    });

    sse.addEventListener('remediation_ready', (e: MessageEvent) => {
      const data = JSON.parse(e.data);
      setChosenCauseId(data.chosen_cause_id);
      setVerificationBadges(data.verification_badges);
      setRemediationPlan(data.remediation_plan);
      setMetrics(data.metrics);
      setIsRunning(false);
      sse.close();
    });

    sse.onerror = (err) => {
      console.error('SSE connection closed or errored', err);
      setIsRunning(false);
      sse.close();
    };
  };

  // Find cause node label if available
  const chosenNode = graphNodes.find((n) => n.id === chosenCauseId);
  const chosenLabel = chosenNode ? (chosenNode.data as any)?.label : chosenCauseId;
  const chosenLink = chosenNode ? (chosenNode.data as any)?.sourceLink : null;

  return (
    <div className="min-h-screen bg-[#070b14] flex flex-col">
      {/* Header */}
      <Header
        mode={mode}
        onModeToggle={(m) => setMode(m)}
        onOpenBenchmarks={() => setIsBenchmarksOpen(true)}
        onOpenAuditLog={() => setIsAuditLogOpen(true)}
        isRunning={isRunning}
      />

      {/* Incident Picker (Hero & Benchmark Scenarios) */}
      <IncidentPicker
        incidents={incidents}
        selectedIncidentId={selectedIncidentId}
        onSelectIncident={handleSelectIncident}
        onRunInvestigation={runInvestigation}
        isRunning={isRunning}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col">
        {/* Split Compare View: Naive RAG vs Enigma */}
        <CompareView
          naiveRag={naiveRag}
          chosenCauseId={chosenCauseId}
          chosenCauseLabel={chosenLabel}
          chosenCauseLink={chosenLink}
          verificationBadges={verificationBadges}
          remediationPlan={remediationPlan}
          onOpenRemediation={() => setIsRemediationOpen(true)}
          isLoading={isRunning}
        />

        {/* Live Metrics Bar when available */}
        {metrics && (
          <div className="px-6 py-2 bg-slate-900/60 border-b border-slate-800 flex items-center justify-between text-xs font-mono text-slate-300">
            <div className="flex items-center space-x-4">
              <span className="flex items-center space-x-1.5 text-emerald-400">
                <Sparkles className="w-3.5 h-3.5" />
                <span>ADK Multi-Agent Run Completed</span>
              </span>
              <span>Tokens: {metrics.tokens_used.toLocaleString()}</span>
              <span>Cost: ${metrics.cost_usd.toFixed(5)}</span>
              <span>Time: {metrics.latency_seconds}s</span>
            </div>

            <div className="flex items-center space-x-2 text-[11px] text-slate-400">
              <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                Mode: {metrics.mode.toUpperCase()}
              </span>
              <span>Firestore Sync: Active</span>
            </div>
          </div>
        )}

        {/* Interactive Causal Graph */}
        <div className="flex-1 min-h-[460px] relative">
          <CausalGraph nodes={graphNodes} edges={graphEdges} />
        </div>

        {/* Live Turn-by-Turn Debate Drawer */}
        <DebateDrawer
          messages={agentMessages}
          isOpen={isDebateOpen}
          onToggle={() => setIsDebateOpen(!isDebateOpen)}
        />
      </div>

      {/* Remediation PR & Human Approval Modal */}
      {isRemediationOpen && remediationPlan && (
        <RemediationModal
          plan={remediationPlan}
          incidentId={selectedIncidentId}
          onClose={() => setIsRemediationOpen(false)}
          onApprovalSuccess={(prUrl) => {
            setRemediationPlan({ ...remediationPlan, approved: true, pr_url: prUrl });
          }}
        />
      )}

      {/* Benchmarks Modal */}
      {isBenchmarksOpen && <BenchmarksModal onClose={() => setIsBenchmarksOpen(false)} />}

      {/* Audit Log Modal */}
      {isAuditLogOpen && <AuditLogModal onClose={() => setIsAuditLogOpen(false)} />}
    </div>
  );
};

export default App;
