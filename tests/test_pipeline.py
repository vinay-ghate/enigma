"""
Unit and integration tests for Enigma agent pipeline and SSE event contract.
"""

import pytest
import json
from backend.agents.pipeline import pipeline
from backend.agents.evidence_agent import EvidenceAgent
from backend.agents.hypothesis_agent import HypothesisAgent
from backend.agents.challenger_agent import ChallengerAgent
from backend.baseline.naive_rag import NaiveRAGBaseline
from backend.data.loader import load_incidents


def test_evidence_agent():
    agent = EvidenceAgent()
    msg, timeline, stale = agent.run("INC-101")
    assert msg.agent == "evidence"
    assert len(timeline) > 0
    assert len(stale) == 1
    assert stale[0]["doc_id"] == "doc-082"


def test_naive_rag_baseline():
    baseline = NaiveRAGBaseline()
    incidents = load_incidents()
    inc1 = next(i for i in incidents if i.id == "INC-101")
    res = baseline.query(inc1)
    assert res["decoy_node_id"] == "pr-409"
    assert "PR #409" in res["retrieved_item"]
    assert "why_it_fails" in res


def test_hypothesis_and_challenger_loop():
    hypo_agent = HypothesisAgent()
    chall_agent = ChallengerAgent()

    # Turn 1
    msg1, hypotheses = hypo_agent.generate_hypotheses("INC-101")
    assert len(hypotheses) >= 1
    assert any(h.cause_node_id == "pr-412" for h in hypotheses)

    # Challenger review
    chall_msg, updated_hypo, ruled_out = chall_agent.challenge_hypotheses("INC-101", hypotheses)
    assert chall_msg.agent == "challenger"
    # Ground truth pr-412 should survive
    surviving = [h for h in updated_hypo if h.cause_node_id == "pr-412"]
    assert len(surviving) == 1
    assert surviving[0].confidence == "high"


@pytest.mark.asyncio
async def test_full_pipeline_stream():
    events_received = []
    async for sse_chunk in pipeline.run_investigation_stream("INC-101", mode="live"):
        lines = sse_chunk.strip().split("\n")
        event_name = ""
        data_json = ""
        for line in lines:
            if line.startswith("event: "):
                event_name = line[7:]
            elif line.startswith("data: "):
                data_json = line[6:]
        if event_name:
            events_received.append((event_name, json.loads(data_json)))

    event_names = [e[0] for e in events_received]
    assert "timeline_ready" in event_names
    assert "naive_rag_ready" in event_names
    assert "agent_message" in event_names
    assert "graph_updated" in event_names
    assert "remediation_ready" in event_names

    # Check remediation
    rem_event = next(e[1] for e in events_received if e[0] == "remediation_ready")
    assert rem_event["passed_hard_checks"] is True
    assert rem_event["chosen_cause_id"] == "pr-412"
    assert rem_event["verification_badges"]["temporal_verified"] is True
    assert rem_event["verification_badges"]["topology_path_exists"] is True
