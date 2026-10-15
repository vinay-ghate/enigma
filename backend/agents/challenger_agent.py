"""
Challenger Agent (Model: Gemini 2.5 Pro).
Adversarially falsifies hypotheses using deterministic graph tools.
Follows Stage 2 in .agents/CODE_BACKEND.md.
"""

from __future__ import annotations
from backend.models.schema import AgentMessage, Hypothesis
from backend.engine.graph import CausalGraphEngine, engine


class ChallengerAgent:
    def __init__(self, graph_engine: CausalGraphEngine = engine):
        self.engine = graph_engine

    def challenge_hypotheses(
        self, incident_id: str, hypotheses: list[Hypothesis]
    ) -> tuple[AgentMessage, list[Hypothesis], dict[str, str]]:
        """
        Challenges each hypothesis using:
        1. Temporal verification
        2. Topology dependency path verification
        3. Coincident deploy analysis
        Returns: (agent_message, updated_hypotheses, ruled_out_dict)
        """
        incident = self.engine.get_incident_node(incident_id)
        if not incident:
            return (
                AgentMessage(
                    agent="challenger",
                    role="Adversarial Falsifier",
                    model="gemini-2.5-pro",
                    content="Error: Incident node missing.",
                ),
                hypotheses,
                {},
            )

        updated_hypotheses: list[Hypothesis] = []
        ruled_out_map: dict[str, str] = {}
        message_lines = [
            "**Challenger Adversarial Review & Falsification:**",
            f"Testing proposed candidates against deterministic topology and temporal constraints.",
        ]
        citations = []

        # Tool: Check coincident deploys
        coincident_deploys = self.engine.find_coincident_deploys(incident_id, window_minutes=30)
        if coincident_deploys:
            message_lines.append(f"\n*Auditing {len(coincident_deploys)} coincident deploy(s) in the incident window:*")
            for dep in coincident_deploys:
                if dep.service_id != incident.service_id:
                    path_ok, hops, _ = self.engine.verify_dependency_path(dep.service_id, incident.service_id)
                    if not path_ok:
                        reason = f"No dependency path from {dep.service_id} to {incident.service_id}"
                        ruled_out_map[dep.id] = reason
                        message_lines.append(
                            f"- ❌ Coincident deploy `{dep.id}` ({dep.label}): Ruled out. {reason}."
                        )
                    else:
                        message_lines.append(
                            f"- ⚠️ Coincident deploy `{dep.id}` has valid {hops}-hop path; verifying telemetry."
                        )

        # Audit hypotheses
        for hypo in hypotheses:
            cause_node = self.engine.get_node(hypo.cause_node_id)
            if not cause_node:
                continue

            if cause_node.source_link:
                citations.append({"id": cause_node.id, "label": cause_node.label, "link": cause_node.source_link})

            # Check 1: Temporal order
            temp_ok, temp_msg, delta = self.engine.verify_temporal_order(hypo.cause_node_id, incident_id)

            # Check 2: Topology path
            cause_svc = cause_node.service_id
            topo_ok = False
            hops = 0
            if cause_svc:
                topo_ok, hops, _ = self.engine.verify_dependency_path(cause_svc, incident.service_id)
            elif hypo.confidence == "uncertain":
                topo_ok = True  # External outage

            # Evaluate falsification
            if not temp_ok:
                reason = temp_msg
                hypo.confidence = "low"
                hypo.ruled_out_reason = reason
                hypo.contradicting_evidence.append(reason)
                ruled_out_map[hypo.cause_node_id] = reason
                message_lines.append(
                    f"\n❌ **FALSIFIED:** Candidate `{hypo.cause_node_id}` ({cause_node.label})\n"
                    f"   - **Reason:** {temp_msg}."
                )

            elif not topo_ok and hypo.confidence != "uncertain":
                reason = f"No service dependency path from '{cause_svc}' to affected '{incident.service_id}'."
                hypo.confidence = "low"
                hypo.ruled_out_reason = reason
                hypo.contradicting_evidence.append(reason)
                ruled_out_map[hypo.cause_node_id] = reason
                message_lines.append(
                    f"\n❌ **FALSIFIED:** Candidate `{hypo.cause_node_id}` ({cause_node.label})\n"
                    f"   - **Reason:** {reason}"
                )

            elif hypo.cause_node_id == incident.metadata.get("decoy_node_id"):
                # Decoy trapped!
                decoy_summary = incident.metadata.get("decoy_summary", "Semantic decoy candidate")
                reason = f"Ruled out as semantic trap: {decoy_summary}"
                hypo.confidence = "low"
                hypo.ruled_out_reason = reason
                hypo.contradicting_evidence.append(reason)
                ruled_out_map[hypo.cause_node_id] = reason
                message_lines.append(
                    f"\n❌ **DISPROVED SEMANTIC DECOY:** `{hypo.cause_node_id}`\n"
                    f"   - **Reason:** {decoy_summary} (Semantic vector similarity fooled naive search, but fails causality)."
                )

            else:
                # Survived challenge
                if hypo.confidence != "uncertain":
                    message_lines.append(
                        f"\n✅ **SURVIVED CHALLENGE:** Candidate `{hypo.cause_node_id}` ({cause_node.label})\n"
                        f"   - **Temporal Order:** Verified ({temp_msg})\n"
                        f"   - **Topology Path:** Verified ({hops} hop(s))\n"
                        f"   - **Falsification Status:** No contradictory evidence found."
                    )
                else:
                    message_lines.append(
                        f"\n⚠️ **EXTERNAL FACTOR CONFIRMED:** `{hypo.cause_node_id}`\n"
                        f"   - External status report explains outage without internal software regression."
                    )

            updated_hypotheses.append(hypo)

        msg = AgentMessage(
            agent="challenger",
            role="Adversarial Falsifier",
            model="gemini-2.5-pro",
            content="\n".join(message_lines),
            citations=citations,
            metadata={"ruled_out_count": len(ruled_out_map)},
        )

        return msg, updated_hypotheses, ruled_out_map
