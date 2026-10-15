# Enigma System Architecture

## Overview
Enigma investigates microservice production incidents by combining Google ADK agents, an in-memory NetworkX causal graph, and deterministic Python hard checks.

```mermaid
flowchart TD
    subgraph Data Layer
        Topology["Deterministic Topology (depends_on)"]
        SeedPRs["Ingested PRs & Commits"]
        Docs["Runbooks & Docs (validity_intervals)"]
        Deploys["Deployment History"]
    end

    subgraph Causal Memory
        NX["NetworkX DiGraph Engine"]
        Topology --> NX
        SeedPRs --> NX
        Docs --> NX
        Deploys --> NX
    end

    subgraph Agent Loop (Google ADK)
        EvAgent["Evidence Agent (Gemini 2.5 Flash)"]
        HypoAgent["Hypothesis Agent (Gemini 2.5 Pro)"]
        ChallAgent["Challenger Agent (Gemini 2.5 Pro)"]
        
        EvAgent -->|Timeline & Stale Docs| HypoAgent
        HypoAgent <-->|Adversarial Falsification| ChallAgent
    end

    subgraph Deterministic Gate
        PythonCheck["Python Hard Checks (verifier.py)"]
        Rule1["cause.timestamp <= incident.timestamp"]
        Rule2["nx.has_path(changed_svc, affected_svc)"]
        Rule3["no higher-ranked unchallenged hypothesis"]
        PythonCheck --- Rule1
        PythonCheck --- Rule2
        PythonCheck --- Rule3
    end

    subgraph Action & Safety
        RemAgent["Remediation Agent (Gemini 2.5 Pro)"]
        ApprovalGate["Human Approval Gate (approval_token)"]
        SandboxPR["Draft Revert PR (enigma-sandbox)"]
        AuditTrail["Immutable Audit Log"]
    end

    NX --> EvAgent
    NX --> HypoAgent
    NX --> ChallAgent
    ChallAgent --> PythonCheck
    PythonCheck -->|Pass| RemAgent
    RemAgent --> ApprovalGate
    ApprovalGate --> SandboxPR
    ApprovalGate --> AuditTrail
```

---

## 1. Core Architecture Principles

### Principle 1: No LLM Hallucinated Graph Edges
Service dependency topology (`depends_on`), deploy artifacts, and commit timestamps are deterministic ground truth. The LLMs are never permitted to synthesize topology edges.

### Principle 2: Hard Checks Gate Remediation
The Remediation Agent **cannot be invoked** unless the candidate cause passes strict Python checks:
```python
# Pure Python check in backend/engine/verifier.py
temporal_ok = (cause_node.timestamp <= incident.timestamp)
topology_ok = nx.has_path(graph, source=changed_service, target=affected_service)
unchallenged_ok = (len(hypothesis.contradicting_evidence) == 0)

passed_hard_checks = temporal_ok and topology_ok and unchallenged_ok
```

### Principle 3: Replay First
Every live investigation run serializes its progressive SSE event stream and final payload into `seed_data/replays/`. If cloud API limits or quotas are hit, `mode="replay"` serves identical turn-by-turn streams instantly.

---

## 2. ADK Agents & Responsibilities

| Agent | Model | Tools | Responsibility |
| :--- | :--- | :--- | :--- |
| **Evidence Agent** | `gemini-2.5-flash` | `get_subgraph_around_incident()`, `find_superseded_docs()` | Chronological facts within window; flags stale docs; zero speculation. |
| **Hypothesis Agent** | `gemini-2.5-pro` | `get_upstream_changes()`, `search_runbooks()` | Proposes candidate causes along dependency paths. |
| **Challenger Agent** | `gemini-2.5-pro` | `verify_temporal_order()`, `verify_dependency_path()`, `find_coincident_deploys()` | Adversarial falsification of proposed claims using graph tools. |
| **Deterministic Gate** | Python Engine | `verify_hypothesis_hard_checks()` | Pure code validation; emits verification badges. |
| **Remediation Agent** | `gemini-2.5-pro` | Diff generator, Runbook patcher | Generates code revert and runbook update diffs. Gated behind human approval. |

---

## 3. SSE Event Streaming Contract (`/api/incidents/{id}/investigate`)

The backend streams events sequentially over Server-Sent Events (SSE):
1. `event: timeline_ready` — Chronological timeline and flagged superseded documents.
2. `event: naive_rag_ready` — Naive vector search baseline for side-by-side comparison.
3. `event: agent_message` — Turn-by-turn debate messages between Evidence, Hypothesis, Challenger, and Verifier.
4. `event: graph_updated` — Causal graph payload formatted with Dagre auto-layout coordinates and state classes.
5. `event: remediation_ready` — Draft PR diff, verification badges, and investigation metrics (latency, tokens, cost).
