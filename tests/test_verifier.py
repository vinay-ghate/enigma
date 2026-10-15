"""
Unit tests for deterministic graph checks and verifier.
"""

import pytest
from backend.engine.graph import CausalGraphEngine
from backend.engine.verifier import verify_hypothesis_hard_checks
from backend.models.schema import Hypothesis


@pytest.fixture
def graph_engine():
    return CausalGraphEngine()


def test_topology_path_verification(graph_engine):
    # recommendationservice -> productcatalogservice
    # When productcatalogservice fails, recommendation is affected
    ok, hops, path = graph_engine.verify_dependency_path(
        source_service="svc-productcatalog",
        target_service="svc-recommendation",
    )
    assert ok is True
    assert hops == 1
    assert path == ["svc-productcatalog", "svc-recommendation"]

    # Ad service has no path to recommendationservice
    ok_ad, _, _ = graph_engine.verify_dependency_path(
        source_service="svc-ad",
        target_service="svc-recommendation",
    )
    assert ok_ad is False


def test_temporal_order_check(graph_engine):
    # PR #412 was merged before INC-101
    ok, msg, delta = graph_engine.verify_temporal_order("pr-412", "INC-101")
    assert ok is True
    assert delta > 0

    # PR #820 was merged AFTER INC-105 started
    ok_future, msg_future, delta_future = graph_engine.verify_temporal_order("pr-820", "INC-105")
    assert ok_future is False
    assert delta_future < 0
    assert "Temporal violation" in msg_future


def test_superseded_doc_detection(graph_engine):
    stale = graph_engine.find_superseded_docs(service_id="svc-recommendation")
    assert len(stale) == 1
    assert stale[0]["doc_id"] == "doc-082"
    assert stale[0]["superseded_by"] == "pr-412"


def test_verifier_gates_valid_hypothesis(graph_engine):
    valid_hypo = Hypothesis(
        id="hypo-1",
        incident_id="INC-101",
        cause_node_id="pr-412",
        confidence="high",
        causal_path=["pr-412", "svc-recommendation", "svc-frontend"],
        supporting_evidence=["Merged 14m before incident", "Directly lowered TTL from 300s to 5s"],
        contradicting_evidence=[],
        unresolved_gaps=[],
        falsifiers=[],
    )
    passed, badges, failures = verify_hypothesis_hard_checks(valid_hypo, graph_engine)
    assert passed is True
    assert badges.temporal_verified is True
    assert badges.topology_path_exists is True
    assert badges.stale_doc_detected is True
    assert len(failures) == 0


def test_verifier_rejects_temporal_violation(graph_engine):
    invalid_hypo = Hypothesis(
        id="hypo-2",
        incident_id="INC-105",
        cause_node_id="pr-820",  # Merged after incident!
        confidence="high",
        causal_path=["pr-820", "svc-frontend"],
        supporting_evidence=["Matches service name"],
        contradicting_evidence=[],
        unresolved_gaps=[],
        falsifiers=[],
    )
    passed, badges, failures = verify_hypothesis_hard_checks(invalid_hypo, graph_engine)
    assert passed is False
    assert badges.temporal_verified is False
    assert any("Temporal violation" in f for f in failures)
