export interface Incident {
  id: string;
  title: string;
  service_id: string;
  severity: 'critical' | 'high' | 'medium';
  timestamp: string;
  description: string;
  trap_type: string;
  is_hero: boolean;
}

export interface VerificationBadges {
  temporal_verified: boolean;
  temporal_delta_seconds?: number;
  topology_path_exists: boolean;
  topology_path_hops: number;
  topology_path: string[];
  stale_doc_detected: boolean;
  superseded_doc_id?: string;
  superseded_by_id?: string;
  no_higher_ranked_unchallenged: boolean;
}

export interface RemediationPlan {
  incident_id: string;
  target_repo: string;
  pr_title: string;
  pr_branch: string;
  pr_body: string;
  diff_preview: string;
  runbook_patch?: string;
  approved: boolean;
  pr_url?: string;
}

export interface AgentMessage {
  agent: 'evidence' | 'hypothesis' | 'challenger' | 'verifier' | 'remediation' | 'system';
  role: string;
  model: 'gemini-2.5-flash' | 'gemini-2.5-pro' | 'deterministic-engine';
  content: string;
  timestamp: string;
  citations: { id: string; label: string; link: string }[];
  metadata?: Record<string, any>;
}

export interface NaiveRAGResult {
  incident_id: string;
  baseline_model: string;
  retrieved_item: string;
  source_link?: string;
  similarity_score: number;
  verdict: string;
  proposed_remediation: string;
  trap_type: string;
  why_it_fails: string;
  decoy_node_id: string;
}

export interface TimelineNode {
  id: string;
  type: string;
  label: string;
  timestamp?: string;
  service_id?: string;
  source_link?: string;
}

export interface GraphNodeData {
  id: string;
  label: string;
  nodeType: string;
  state: 'normal' | 'incident' | 'chosen_cause' | 'ruled_out_candidate' | 'superseded_doc';
  timestamp?: string;
  serviceId?: string;
  sourceLink?: string;
  supersededBy?: string;
  ruledOutReason?: string;
  metadata?: Record<string, any>;
}

export interface InvestigationMetrics {
  tokens_used: number;
  cost_usd: number;
  latency_seconds: number;
  mode: 'live' | 'replay';
}
