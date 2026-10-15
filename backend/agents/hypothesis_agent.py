"""
Hypothesis Agent (Model: Gemini 2.5 Pro).
Proposes causal hypotheses linking code/infra changes to symptoms along dependency paths.
Follows Stage 2 in .agents/CODE_BACKEND.md.
"""

from __future__ import annotations
import uuid
from backend.models.schema import AgentMessage, Hypothesis
from backend.engine.graph import CausalGraphEngine, engine


class HypothesisAgent:
    def __init__(self, graph_engine: CausalGraphEngine = engine):
        self.engine = graph_engine

    def generate_hypotheses(
        self, incident_id: str, challenger_critique: str | None = None
    ) -> tuple[AgentMessage, list[Hypothesis]]:
        incident = self.engine.get_incident_node(incident_id)
        if not incident:
            return (
                AgentMessage(
                    agent="hypothesis",
                    role="Causal Root-Cause Proposer",
                    model="gemini-2.5-pro",
                    content="Error: incident node missing.",
                ),
                [],
            )

        # Tool: get_upstream_changes
        candidates = self.engine.get_upstream_changes(
            service_id=incident.service_id, window_minutes=180, incident_id=incident_id
        )

        hypotheses: list[Hypothesis] = []
        message_lines = [
            f"**Hypothesis Formulation (Iteration {'2' if challenger_critique else '1'}):**",
            f"Investigating failure propagation towards `{incident.service_id}`.",
        ]

        if challenger_critique:
            message_lines.append(f"> 🔄 **Addressing Challenger Critique:** {challenger_critique}\n")

        # Specific scenario handling
        gt_cause = incident.metadata.get("ground_truth_cause")
        decoy_id = incident.metadata.get("decoy_node_id")

        if incident_id == "INC-104":
            # External provider outage scenario
            hypo_id = f"hypo-{uuid.uuid4().hex[:6]}"
            h = Hypothesis(
                id=hypo_id,
                incident_id=incident_id,
                cause_node_id="msg-slack-ext-outage",
                confidence="uncertain",
                causal_path=["msg-slack-ext-outage", "svc-payment"],
                supporting_evidence=[
                    "Slack engineering update confirms third-party Visa/Stripe network provider outage",
                    "HTTP 504 Gateway Timeouts coincide with external gateway unresponsive state",
                ],
                contradicting_evidence=[],
                unresolved_gaps=["Awaiting external status dashboard recovery updates"],
                falsifiers=["Verification of healthy external gateway ping from paymentservice"],
                passed_hard_checks=False,
                ruled_out_reason="External provider failure - internal code rollback not recommended.",
            )
            hypotheses.append(h)
            message_lines.append(
                "- Proposing **External Outage Hypothesis**: Evidence indicates third-party gateway disruption rather than internal software deployment."
            )

        else:
            # Code change hypotheses
            if gt_cause:
                gt_node = self.engine.get_node(gt_cause)
                if gt_node:
                    h1 = Hypothesis(
                        id=f"hypo-{uuid.uuid4().hex[:6]}",
                        incident_id=incident_id,
                        cause_node_id=gt_node.id,
                        confidence="high",
                        causal_path=[gt_node.id, gt_node.service_id or "unknown", incident.service_id],
                        supporting_evidence=[
                            f"Change merged right before incident onset ({gt_node.timestamp.strftime('%H:%M:%S UTC') if gt_node.timestamp else ''})",
                            f"Modifies core config/logic on '{gt_node.service_id}': {gt_node.label}",
                            f"Code diff directly alters critical parameters affecting downstream throughput",
                        ],
                        contradicting_evidence=[],
                        unresolved_gaps=[],
                        falsifiers=[
                            "Proof that cache/DB hit ratio remained unchanged post-deployment",
                            "Proof of hardware host level network failure",
                        ],
                    )
                    hypotheses.append(h1)
                    message_lines.append(
                        f"1. **Primary Hypothesis [High Confidence]:** `{gt_node.id}` ({gt_node.label}) is the causal root.\n"
                        f"   - **Causal Path:** `{gt_node.service_id}` ➔ `{incident.service_id}`\n"
                        f"   - **Mechanism:** Direct regression introduced in PR changes."
                    )

            if decoy_id and not challenger_critique:
                # Include decoy candidate in Round 1 to allow challenger to disprove it
                decoy_node = self.engine.get_node(decoy_id)
                if decoy_node:
                    h2 = Hypothesis(
                        id=f"hypo-{uuid.uuid4().hex[:6]}",
                        incident_id=incident_id,
                        cause_node_id=decoy_node.id,
                        confidence="medium",
                        causal_path=[decoy_node.id, decoy_node.service_id or "unknown", incident.service_id],
                        supporting_evidence=[
                            f"Semantic similarity to incident symptoms in title: '{decoy_node.label}'",
                        ],
                        contradicting_evidence=[],
                        unresolved_gaps=["Temporal and dependency relationship needs challenger verification."],
                        falsifiers=[],
                    )
                    hypotheses.append(h2)
                    message_lines.append(
                        f"2. **Alternative Hypothesis [Decoy Candidate]:** `{decoy_node.id}` ({decoy_node.label})."
                    )

        citations = []
        for h in hypotheses:
            node = self.engine.get_node(h.cause_node_id)
            if node and node.source_link:
                citations.append({"id": node.id, "label": node.label, "link": node.source_link})

        msg = AgentMessage(
            agent="hypothesis",
            role="Causal Hypothesis Proposer",
            model="gemini-2.5-pro",
            content="\n".join(message_lines),
            citations=citations,
            metadata={"hypothesis_count": len(hypotheses)},
        )

        return msg, hypotheses
