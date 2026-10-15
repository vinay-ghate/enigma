# Backend & Google ADK Coding Agent Guidelines

## Stack & Conventions
- Python 3.12, `uv`, FastAPI, Pydantic v2, `google-adk`, `google-genai`, `networkx`[cite: 1].
- Use `ruff` for linting/formatting. Type-hint all function signatures.
- All I/O endpoints (Firestore, Vertex AI Search, GitHub API, Gemini calls) must be async or wrapped cleanly for FastAPI SSE streaming[cite: 1].

## Canonical Data Models (`backend/models/schema.py`)
Enforce these exact fields across Firestore, NetworkX, and API responses[cite: 1]:
- `Node`: `id: str`, `type: Literal["pr", "deploy", "ticket", "message", "doc", "service", "incident"]`, `timestamp: datetime | None`, `service_id: str | None`, `source_link: str`, `validity_interval: tuple[datetime, datetime | None]`, `superseded_by: str | None`, `metadata: dict`[cite: 1].
- `Edge`: `source: str`, `target: str`, `type: Literal["modifies", "depends_on", "caused_by_candidate", "supersedes", "discussed_in"]`, `evidence: str`[cite: 1].
- `Hypothesis`: `id: str`, `incident_id: str`, `cause_node_id: str`, `confidence: Literal["high", "medium", "low", "uncertain"]`, `causal_path: list[str]`, `supporting_evidence: list[str]`, `contradicting_evidence: list[str]`, `unresolved_gaps: list[str]`, `falsifiers: list[str]`, `passed_hard_checks: bool`, `ruled_out_reason: str | None`[cite: 1].

## ADK Pipeline Implementation (`backend/agents/`)
Implement the 4-stage pipeline using Google ADK[cite: 1]:
1. **Evidence Agent (`gemini-2.5-flash`):**
   - Input: `incident_id` and time window.
   - Tools: `get_subgraph_around_incident()`, `find_superseded_docs()`.
   - Rule: Output strictly chronological facts and flag any doc where `superseded_by is not None`[cite: 1]. Zero speculation[cite: 1].
2. **Hypothesis <-> Challenger Loop (`LoopAgent`, max_iterations=2, `gemini-2.5-pro`):**
   - **Hypothesis Agent Tools:** `get_upstream_changes(service_id, window_minutes)`, `search_runbooks(query)`.
   - **Challenger Agent Tools:** `verify_temporal_order(change_id, incident_id)`, `verify_dependency_path(source_service, target_service)`, `find_coincident_deploys(window_minutes)`.
   - Rule: Challenger must actively try to falsify the Hypothesis Agent's top claim using graph tools and populate `contradicting_evidence` and `falsifiers`[cite: 1].
3. **Deterministic Gate (`backend/engine/verifier.py`):**
   - Pure Python check between Challenger loop and Remediation Agent[cite: 1].
   - Computes `passed_hard_checks` and attaches verification badges (`temporal_verified`, `topology_path_hops`, `stale_doc_detected`).
4. **Remediation Agent (`gemini-2.5-pro`):**
   - Only runs if `passed_hard_checks == True`[cite: 1].
   - Generates a revert/fix diff preview, incident summary, and stale runbook update flag[cite: 1]. Does NOT call GitHub API until `/api/incidents/{id}/approve` is triggered by a human[cite: 1].

## SSE Event Contract (`/api/incidents/{id}/investigate`)
Stream JSON events in this exact order so the frontend renders progressively:
- `event: timeline_ready` -> Timeline nodes + stale doc flags[cite: 1]
- `event: naive_rag_ready` -> Baseline Vertex AI Search + Gemini output for side-by-side comparison[cite: 1]
- `event: agent_message` -> Live turn-by-turn exchange (Hypothesis & Challenger)[cite: 1]
- `event: graph_updated` -> Highlighted causal path + ruled-out decoy nodes with reasons[cite: 1]
- `event: remediation_ready` -> Proposed PR diff + metrics (tokens, cost, latency)[cite: 1]