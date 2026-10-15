"""
Deterministic Hard Checks Verifier.
Strict Python verification gating the Remediation Agent.
Follows Core Architecture Rule #3 in AGENTS.md.
"""

from __future__ import annotations
from backend.models.schema import Hypothesis, VerificationBadges, Node
from backend.engine.graph import CausalGraphEngine, engine


def verify_hypothesis_hard_checks(
    hypothesis: Hypothesis,
    graph_engine: CausalGraphEngine = engine,
) -> tuple[bool, VerificationBadges, list[str]]:
    """
    Runs deterministic Python checks against candidate cause node:
    1. Temporal check: cause_node.timestamp <= incident.timestamp
    2. Dependency path check: nx.has_path(graph, source=changed_service, target=affected_service)
    3. Stale doc check: flags if any superseded doc is referenced in the incident context
    4. Unchallenged check: ensures no higher-ranked hypothesis exists with contradictory evidence

    Returns: (passed: bool, badges: VerificationBadges, failure_reasons: list[str])
    """
    failures: list[str] = []
    incident = graph_engine.get_incident_node(hypothesis.incident_id)
    cause_node = graph_engine.get_node(hypothesis.cause_node_id)

    if not incident:
        return False, VerificationBadges(
            temporal_verified=False,
            topology_path_exists=False,
            no_higher_ranked_unchallenged=False,
        ), [f"Incident '{hypothesis.incident_id}' not found in graph."]

    if not cause_node:
        return False, VerificationBadges(
            temporal_verified=False,
            topology_path_exists=False,
            no_higher_ranked_unchallenged=False,
        ), [f"Cause candidate node '{hypothesis.cause_node_id}' not found in graph."]

    # 1. Temporal Check: cause_node.timestamp <= incident.timestamp
    temporal_ok, temporal_msg, delta_secs = graph_engine.verify_temporal_order(
        change_id=cause_node.id,
        incident_id=incident.id,
    )
    if not temporal_ok:
        failures.append(temporal_msg)

    # 2. Topology Check: Path exists from changed service to affected service
    changed_service = cause_node.service_id
    affected_service = incident.service_id

    if not changed_service or not affected_service:
        # If cause is a generic message or external outage, check if it directly names the service
        topology_ok = (changed_service == affected_service)
        hops = 0
        path = [changed_service or "unknown"]
    else:
        topology_ok, hops, path = graph_engine.verify_dependency_path(
            source_service=changed_service,
            target_service=affected_service,
        )

    if not topology_ok:
        failures.append(
            f"No service dependency path exists from '{changed_service}' to affected '{affected_service}'."
        )

    # 3. Superseded / Stale Document Check
    stale_docs = graph_engine.find_superseded_docs(service_id=affected_service)
    stale_detected = len(stale_docs) > 0
    superseded_doc_id = stale_docs[0]["doc_id"] if stale_detected else None
    superseded_by_id = stale_docs[0]["superseded_by"] if stale_detected else None

    # 4. Challenger Check
    no_higher_unchallenged = (
        hypothesis.confidence in ["high", "medium"]
        and len(hypothesis.contradicting_evidence) == 0
    )
    if not no_higher_unchallenged and len(hypothesis.contradicting_evidence) > 0:
        failures.append(
            f"Challenger found {len(hypothesis.contradicting_evidence)} contradictory evidence points."
        )

    passed_all = (
        temporal_ok
        and topology_ok
        and (hypothesis.confidence != "uncertain")
        and len(failures) == 0
    )

    badges = VerificationBadges(
        temporal_verified=temporal_ok,
        temporal_delta_seconds=delta_secs,
        topology_path_exists=topology_ok,
        topology_path_hops=hops,
        topology_path=path,
        stale_doc_detected=stale_detected,
        superseded_doc_id=superseded_doc_id,
        superseded_by_id=superseded_by_id,
        no_higher_ranked_unchallenged=no_higher_unchallenged,
    )

    return passed_all, badges, failures
