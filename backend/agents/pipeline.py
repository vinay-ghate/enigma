"""
Enigma ADK Pipeline Coordinator.
Orchestrates Evidence -> Hypothesis <-> Challenger -> Hard Checks Gate -> Remediation.
Implements the strict SSE Event Contract.
"""

from __future__ import annotations
import json
import asyncio
import time
from typing import AsyncGenerator
from backend.models.schema import (
    InvestigationRun,
    Hypothesis,
    VerificationBadges,
    RemediationPlan,
    AgentMessage,
)
from backend.engine.graph import CausalGraphEngine, engine
from backend.engine.verifier import verify_hypothesis_hard_checks
from backend.baseline.naive_rag import NaiveRAGBaseline
from backend.agents.evidence_agent import EvidenceAgent
from backend.agents.hypothesis_agent import HypothesisAgent
from backend.agents.challenger_agent import ChallengerAgent
from backend.agents.remediation_agent import RemediationAgent
from backend.data.loader import load_incidents


class EnigmaPipeline:
    def __init__(self, graph_engine: CausalGraphEngine = engine):
        self.engine = graph_engine
        self.baseline = NaiveRAGBaseline(graph_engine)
        self.evidence_agent = EvidenceAgent(graph_engine)
        self.hypothesis_agent = HypothesisAgent(graph_engine)
        self.challenger_agent = ChallengerAgent(graph_engine)
        self.remediation_agent = RemediationAgent(graph_engine)

    async def run_investigation_stream(
        self, incident_id: str, mode: str = "live"
    ) -> AsyncGenerator[str, None]:
        """
        Executes investigation pipeline and streams SSE formatted events:
        - timeline_ready
        - naive_rag_ready
        - agent_message (turn by turn)
        - graph_updated
        - remediation_ready
        """
        start_time = time.time()
        incident = self.engine.get_incident_node(incident_id)
        if not incident:
            yield f"event: error\ndata: {json.dumps({'error': f'Incident {incident_id} not found'})}\n\n"
            return

        incidents_list = load_incidents()
        incident_summary = next((i for i in incidents_list if i.id == incident_id), None)

        tokens_counter = 0
        cost_counter = 0.0

        # -------------------------------------------------------------
        # STEP 1: Evidence Gathering (Flash)
        # -------------------------------------------------------------
        ev_msg, timeline_nodes, stale_docs = self.evidence_agent.run(incident_id)
        tokens_counter += 420
        cost_counter += 0.000105

        timeline_payload = {
            "incident_id": incident_id,
            "timeline": [
                {
                    "id": n.id,
                    "type": n.type,
                    "label": n.label,
                    "timestamp": n.timestamp.isoformat() if n.timestamp else None,
                    "service_id": n.service_id,
                    "source_link": n.source_link,
                }
                for n in timeline_nodes
            ],
            "stale_docs": stale_docs,
        }
        yield f"event: timeline_ready\ndata: {json.dumps(timeline_payload)}\n\n"
        await asyncio.sleep(0.3)

        # -------------------------------------------------------------
        # STEP 2: Naive RAG Baseline Calculation
        # -------------------------------------------------------------
        if incident_summary:
            naive_rag_data = self.baseline.query(incident_summary)
        else:
            naive_rag_data = {"error": "Incident summary not found"}

        yield f"event: naive_rag_ready\ndata: {json.dumps(naive_rag_data)}\n\n"
        await asyncio.sleep(0.3)

        # Stream Evidence Agent Message
        yield f"event: agent_message\ndata: {json.dumps(ev_msg.model_dump(mode='json'))}\n\n"
        await asyncio.sleep(0.4)

        # -------------------------------------------------------------
        # STEP 3: Hypothesis <-> Challenger Loop (Pro, max 2 turns)
        # -------------------------------------------------------------
        # Turn 1: Hypothesis
        hypo_msg1, hypotheses1 = self.hypothesis_agent.generate_hypotheses(incident_id)
        tokens_counter += 850
        cost_counter += 0.0017
        yield f"event: agent_message\ndata: {json.dumps(hypo_msg1.model_dump(mode='json'))}\n\n"
        await asyncio.sleep(0.5)

        # Turn 2: Challenger Falsification
        chall_msg1, updated_hypo1, ruled_out_map = self.challenger_agent.challenge_hypotheses(
            incident_id, hypotheses1
        )
        tokens_counter += 920
        cost_counter += 0.00184
        yield f"event: agent_message\ndata: {json.dumps(chall_msg1.model_dump(mode='json'))}\n\n"
        await asyncio.sleep(0.5)

        # Find top surviving hypothesis
        surviving = [h for h in updated_hypo1 if h.confidence in ["high", "medium"]]
        top_hypo = surviving[0] if surviving else (updated_hypo1[0] if updated_hypo1 else None)

        chosen_cause_id = top_hypo.cause_node_id if top_hypo else None

        # -------------------------------------------------------------
        # STEP 4: Hard Checks Verifier Gate
        # -------------------------------------------------------------
        passed_hard_checks = False
        badges = None
        failures = []

        if top_hypo:
            passed_hard_checks, badges, failures = verify_hypothesis_hard_checks(
                top_hypo, self.engine
            )
            top_hypo.passed_hard_checks = passed_hard_checks

        # Emit verifier agent message
        verifier_content = (
            f"**Deterministic Gate Status:** {'✅ PASSED' if passed_hard_checks else '⚠️ BLOCKED'}\n"
            f"- Temporal Precedence: {'Passed' if badges and badges.temporal_verified else 'Failed'}\n"
            f"- Topological Dependency Path: {'Passed (' + str(badges.topology_path_hops) + ' hops)' if badges and badges.topology_path_exists else 'Failed'}\n"
            f"- Documentation Validity: {'Stale Doc Detected' if badges and badges.stale_doc_detected else 'Clean'}\n"
        )
        if failures:
            verifier_content += f"\n*Failures/Notes:* {'; '.join(failures)}"

        verifier_msg = AgentMessage(
            agent="verifier",
            role="Deterministic Gate",
            model="deterministic-engine",
            content=verifier_content,
            metadata={"passed": passed_hard_checks},
        )
        yield f"event: agent_message\ndata: {json.dumps(verifier_msg.model_dump(mode='json'))}\n\n"
        await asyncio.sleep(0.3)

        # -------------------------------------------------------------
        # STEP 5: Graph Update (Causal Path & Ruled Out Candidates)
        # -------------------------------------------------------------
        graph_data = self.engine.export_graph_for_ui(
            incident_id=incident_id,
            chosen_cause_id=chosen_cause_id if passed_hard_checks else None,
            ruled_out_ids=ruled_out_map,
        )
        yield f"event: graph_updated\ndata: {json.dumps(graph_data)}\n\n"
        await asyncio.sleep(0.3)

        # -------------------------------------------------------------
        # STEP 6: Remediation Agent (Only if passed_hard_checks)
        # -------------------------------------------------------------
        remediation_plan = None
        if passed_hard_checks and top_hypo and badges:
            rem_msg, remediation_plan = self.remediation_agent.draft_remediation(
                incident_id=incident_id,
                hypothesis=top_hypo,
                verification=badges,
            )
            tokens_counter += 1150
            cost_counter += 0.0023
            yield f"event: agent_message\ndata: {json.dumps(rem_msg.model_dump(mode='json'))}\n\n"
            await asyncio.sleep(0.4)

        elapsed = time.time() - start_time
        remediation_payload = {
            "incident_id": incident_id,
            "passed_hard_checks": passed_hard_checks,
            "chosen_cause_id": chosen_cause_id if passed_hard_checks else None,
            "verification_badges": badges.model_dump() if badges else None,
            "remediation_plan": remediation_plan.model_dump() if remediation_plan else None,
            "metrics": {
                "tokens_used": tokens_counter,
                "cost_usd": round(cost_counter, 6),
                "latency_seconds": round(elapsed, 2),
                "mode": mode,
            },
        }
        yield f"event: remediation_ready\ndata: {json.dumps(remediation_payload)}\n\n"


# Singleton pipeline instance
pipeline = EnigmaPipeline()
