"""
Evidence Agent (Model: Gemini 2.5 Flash).
Gathers chronological events around incident window without speculation.
Follows Stage 1 in .agents/CODE_BACKEND.md.
"""

from __future__ import annotations
from datetime import datetime
from backend.models.schema import AgentMessage, Node
from backend.engine.graph import CausalGraphEngine, engine


class EvidenceAgent:
    def __init__(self, graph_engine: CausalGraphEngine = engine):
        self.engine = graph_engine

    def run(self, incident_id: str) -> tuple[AgentMessage, list[Node], list[dict]]:
        incident = self.engine.get_incident_node(incident_id)
        if not incident:
            return (
                AgentMessage(
                    agent="evidence",
                    role="Chronological Fact Gathering",
                    model="gemini-2.5-flash",
                    content=f"Error: Incident {incident_id} not found.",
                ),
                [],
                [],
            )

        # Tool 1: Subgraph around incident
        timeline_nodes = self.engine.get_subgraph_around_incident(incident_id, window_minutes=180)

        # Tool 2: Superseded docs
        stale_docs = self.engine.find_superseded_docs(service_id=incident.service_id)

        # Build chronological factual summary
        fact_lines = [
            f"**Incident Alert Received:** `{incident.id}` on service `{incident.service_id}` at `{incident.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}`.",
            f"**Observed Symptom:** {incident.metadata.get('description', '')}",
            f"**Chronological Events within Inspection Window (T-180m to T+15m):**",
        ]

        citations = []
        for n in timeline_nodes:
            if n.type in ["pr", "deploy", "message", "ticket"]:
                time_str = n.timestamp.strftime("%H:%M:%S UTC") if n.timestamp else "N/A"
                fact_lines.append(f"- `[{time_str}]` **{n.type.upper()}**: {n.label}")
                if n.source_link:
                    citations.append({"id": n.id, "label": n.label, "link": n.source_link})

        if stale_docs:
            fact_lines.append("\n**⚠️ Documentation Validity Alert:**")
            for d in stale_docs:
                fact_lines.append(
                    f"- Flagged stale runbook: `{d['title']}` (ID: `{d['doc_id']}`) is marked **SUPERSEDED** by `{d['superseded_by_label']}`."
                )
                if d.get("source_link"):
                    citations.append({"id": d["doc_id"], "label": d["title"], "link": d["source_link"]})

        message = AgentMessage(
            agent="evidence",
            role="Timeline & Fact Gathering",
            model="gemini-2.5-flash",
            content="\n".join(fact_lines),
            citations=citations,
            metadata={"node_count": len(timeline_nodes), "stale_doc_count": len(stale_docs)},
        )

        return message, timeline_nodes, stale_docs
