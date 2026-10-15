"""
Naive RAG Baseline Simulator for Enigma.
Simulates standard semantic search (e.g. Vertex AI Search / embedding retrieval)
demonstrating how naive vector similarity falls into the 'Semantic Trap'.
"""

from __future__ import annotations
from backend.models.schema import IncidentSummary
from backend.engine.graph import CausalGraphEngine, engine


class NaiveRAGBaseline:
    def __init__(self, graph_engine: CausalGraphEngine = engine):
        self.engine = graph_engine

    def query(self, incident: IncidentSummary) -> dict:
        """
        Executes naive semantic search on the incident description.
        Returns the top retrieved document/PR and explains why naive RAG picked it.
        """
        decoy_node = self.engine.get_node(incident.decoy_node_id)
        decoy_label = decoy_node.label if decoy_node else incident.decoy_node_id
        decoy_link = decoy_node.source_link if decoy_node else ""

        # Map each incident to realistic naive semantic search output
        explanations = {
            "INC-101": {
                "top_match_id": incident.decoy_node_id,
                "top_match_title": decoy_label,
                "source_link": decoy_link,
                "similarity_score": 0.89,
                "verdict": "Blames PR #409 due to high semantic embedding similarity with 'cache TTL' and 'latency optimization'.",
                "naive_remediation": "Revert PR #409 (catalog cache query TTL).",
                "why_it_fails": "PR #409 was merged 3 days prior without incident. The actual cause was PR #412 on recommendationservice merged 14 minutes before the alert. Naive RAG lacks temporal order and service dependency checks.",
            },
            "INC-102": {
                "top_match_id": incident.decoy_node_id,
                "top_match_title": decoy_label,
                "source_link": decoy_link,
                "similarity_score": 0.92,
                "verdict": "Blames PR #518 because incident alert mentions 'checkout errors' matching 'checkout error banners'.",
                "naive_remediation": "Revert PR #518 (checkout button click tracking).",
                "why_it_fails": "PR #518 only touched UI telemetry. The root cause was 2 hops downstream in paymentservice (PR #521 fraud timeout). Naive RAG failed to trace multi-hop service topology.",
            },
            "INC-103": {
                "top_match_id": incident.decoy_node_id,
                "top_match_title": decoy_label,
                "source_link": decoy_link,
                "similarity_score": 0.88,
                "verdict": "Matches RUNBOOK-CART-04 which recommends increasing pod container memory limit to 512Mi.",
                "naive_remediation": "Apply RUNBOOK-CART-04: Bump pod memory to 512Mi.",
                "why_it_fails": "RUNBOOK-CART-04 was superseded 5 months ago by PR #590 when cart migrated to remote Redis. The true cause was PR #633 reducing redis connection pool size. Following stale docs causes repeat crashloop.",
            },
            "INC-104": {
                "top_match_id": incident.decoy_node_id,
                "top_match_title": decoy_label,
                "source_link": decoy_link,
                "similarity_score": 0.86,
                "verdict": "Blames PR #701 ('paymentservice: update payment retry policy') due to 'payment retry' keywords.",
                "naive_remediation": "Revert PR #701 retry policy.",
                "why_it_fails": "PR #701 was merged 14 days ago and was perfectly stable. The real issue is a major external third-party Visa/Stripe regional outage. Naive RAG generates false internal attribution.",
            },
            "INC-105": {
                "top_match_id": incident.decoy_node_id,
                "top_match_title": decoy_label,
                "source_link": decoy_link,
                "similarity_score": 0.91,
                "verdict": "Blames PR #820 due to exact service name match ('frontend') and recent commit activity.",
                "naive_remediation": "Revert PR #820 promo banner.",
                "why_it_fails": "PR #820 was merged 5 minutes AFTER the incident started (violates temporal causality). The real cause is PR #815 in productcatalogservice causing an unindexed database query.",
            },
        }

        default_explanation = {
            "top_match_id": incident.decoy_node_id,
            "top_match_title": decoy_label,
            "source_link": decoy_link,
            "similarity_score": 0.85,
            "verdict": f"Semantic search matched keywords in {decoy_label}.",
            "naive_remediation": f"Revert {incident.decoy_node_id}.",
            "why_it_fails": "Naive RAG ignores causal topology, timestamps, and validity intervals.",
        }

        res = explanations.get(incident.id, default_explanation)
        return {
            "incident_id": incident.id,
            "baseline_model": "Vertex AI Search + Gemini (Naive RAG)",
            "retrieved_item": res["top_match_title"],
            "source_link": res["source_link"],
            "similarity_score": res["similarity_score"],
            "verdict": res["verdict"],
            "proposed_remediation": res["naive_remediation"],
            "trap_type": incident.trap_type,
            "why_it_fails": res["why_it_fails"],
            "decoy_node_id": incident.decoy_node_id,
        }
