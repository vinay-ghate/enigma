"""
Canonical Data Models for Enigma Root-Cause Engine.
Strictly adheres to .agents/CODE_BACKEND.md and Pydantic v2.
"""

from __future__ import annotations
from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel, Field


NodeType = Literal["pr", "deploy", "ticket", "message", "doc", "service", "incident"]
EdgeType = Literal["modifies", "depends_on", "caused_by_candidate", "supersedes", "discussed_in"]
ConfidenceLevel = Literal["high", "medium", "low", "uncertain"]


def current_utc_time() -> datetime:
    return datetime.now(timezone.utc)


class Node(BaseModel):
    id: str
    type: NodeType
    label: str = ""
    timestamp: datetime | None = None
    service_id: str | None = None
    source_link: str = ""
    validity_interval: tuple[datetime | None, datetime | None] = (None, None)
    superseded_by: str | None = None
    metadata: dict = Field(default_factory=dict)


class Edge(BaseModel):
    source: str
    target: str
    type: EdgeType
    evidence: str = ""
    metadata: dict = Field(default_factory=dict)


class Hypothesis(BaseModel):
    id: str
    incident_id: str
    cause_node_id: str
    confidence: ConfidenceLevel
    causal_path: list[str] = Field(default_factory=list)
    supporting_evidence: list[str] = Field(default_factory=list)
    contradicting_evidence: list[str] = Field(default_factory=list)
    unresolved_gaps: list[str] = Field(default_factory=list)
    falsifiers: list[str] = Field(default_factory=list)
    passed_hard_checks: bool = False
    ruled_out_reason: str | None = None


class VerificationBadges(BaseModel):
    temporal_verified: bool
    temporal_delta_seconds: float | None = None
    topology_path_exists: bool
    topology_path_hops: int = 0
    topology_path: list[str] = Field(default_factory=list)
    stale_doc_detected: bool = False
    superseded_doc_id: str | None = None
    superseded_by_id: str | None = None
    no_higher_ranked_unchallenged: bool = True


class RemediationPlan(BaseModel):
    incident_id: str
    target_repo: str = "enigma-sandbox"
    pr_title: str
    pr_branch: str
    pr_body: str
    diff_preview: str
    runbook_patch: str | None = None
    approved: bool = False
    pr_url: str | None = None


class AgentMessage(BaseModel):
    agent: Literal["evidence", "hypothesis", "challenger", "verifier", "remediation", "system"]
    role: str
    model: Literal["gemini-2.5-flash", "gemini-2.5-pro", "deterministic-engine"]
    content: str
    timestamp: datetime = Field(default_factory=current_utc_time)
    citations: list[dict] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class InvestigationRun(BaseModel):
    id: str
    incident_id: str
    mode: Literal["live", "replay"]
    timestamp: datetime = Field(default_factory=current_utc_time)
    status: Literal["running", "completed", "failed"]
    agent_messages: list[AgentMessage] = Field(default_factory=list)
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    chosen_cause_id: str | None = None
    verification: VerificationBadges | None = None
    remediation: RemediationPlan | None = None
    naive_rag_result: dict = Field(default_factory=dict)
    tokens_used: int = 0
    cost_usd: float = 0.0
    latency_seconds: float = 0.0


class IncidentSummary(BaseModel):
    id: str
    title: str
    service_id: str
    severity: Literal["critical", "high", "medium"]
    timestamp: datetime
    description: str
    ground_truth_cause: str
    trap_type: str
    decoy_node_id: str
