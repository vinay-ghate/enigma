"""
NetworkX-powered Causal Graph Engine for Enigma.
Enforces deterministic topology, temporal order, and validity checks.
"""

from __future__ import annotations
from datetime import datetime, timedelta
import networkx as nx
from backend.models.schema import Node, Edge
from backend.data.loader import load_nodes_and_edges


class CausalGraphEngine:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.nodes_dict: dict[str, Node] = {}
        self.edges_list: list[Edge] = []
        self.reload()

    def reload(self):
        self.graph.clear()
        self.nodes_dict.clear()
        self.edges_list.clear()

        nodes, edges = load_nodes_and_edges()
        for node in nodes:
            self.nodes_dict[node.id] = node
            self.graph.add_node(
                node.id,
                type=node.type,
                label=node.label,
                timestamp=node.timestamp,
                service_id=node.service_id,
                source_link=node.source_link,
                superseded_by=node.superseded_by,
                metadata=node.metadata,
            )

        for edge in edges:
            self.edges_list.append(edge)
            self.graph.add_edge(
                edge.source,
                edge.target,
                type=edge.type,
                evidence=edge.evidence,
                metadata=edge.metadata,
            )

    def get_node(self, node_id: str) -> Node | None:
        return self.nodes_dict.get(node_id)

    def get_incident_node(self, incident_id: str) -> Node | None:
        node = self.nodes_dict.get(incident_id)
        if node and node.type == "incident":
            return node
        return None

    def get_subgraph_around_incident(self, incident_id: str, window_minutes: int = 180) -> list[Node]:
        """Evidence Agent tool: gathers nodes within chronological window before incident."""
        incident = self.get_incident_node(incident_id)
        if not incident or not incident.timestamp:
            return []

        start_time = incident.timestamp - timedelta(minutes=window_minutes)
        end_time = incident.timestamp + timedelta(minutes=15)

        subgraph_nodes: list[Node] = [incident]
        for node in self.nodes_dict.values():
            if node.id == incident_id:
                continue
            if node.type in ["service", "doc"]:
                subgraph_nodes.append(node)
            elif node.timestamp:
                if start_time <= node.timestamp <= end_time:
                    subgraph_nodes.append(node)

        # Sort chronological
        subgraph_nodes.sort(key=lambda n: n.timestamp or datetime.min)
        return subgraph_nodes

    def find_superseded_docs(self, service_id: str | None = None) -> list[dict]:
        """Find documentation nodes marked as superseded."""
        results = []
        for node in self.nodes_dict.values():
            if node.type == "doc" and node.superseded_by:
                if service_id and node.service_id != service_id:
                    continue
                superseding_node = self.nodes_dict.get(node.superseded_by)
                results.append({
                    "doc_id": node.id,
                    "title": node.label,
                    "service_id": node.service_id,
                    "superseded_by": node.superseded_by,
                    "superseded_by_label": superseding_node.label if superseding_node else node.superseded_by,
                    "content": node.metadata.get("content", ""),
                    "source_link": node.source_link,
                })
        return results

    def verify_temporal_order(self, change_id: str, incident_id: str) -> tuple[bool, str, float | None]:
        """
        Deterministic Python check:
        cause_node.timestamp <= incident.timestamp
        """
        change_node = self.get_node(change_id)
        incident_node = self.get_incident_node(incident_id)

        if not change_node or not change_node.timestamp:
            return False, f"Change node '{change_id}' has no timestamp recorded.", None
        if not incident_node or not incident_node.timestamp:
            return False, f"Incident '{incident_id}' has no timestamp recorded.", None

        delta_seconds = (incident_node.timestamp - change_node.timestamp).total_seconds()
        if delta_seconds < 0:
            abs_min = abs(delta_seconds) / 60.0
            return (
                False,
                f"Temporal violation: Change '{change_id}' occurred {abs_min:.1f} minutes AFTER incident started.",
                delta_seconds,
            )

        mins = delta_seconds / 60.0
        return (
            True,
            f"Temporal order verified: Change merged {mins:.1f} minutes before incident alert.",
            delta_seconds,
        )

    def verify_dependency_path(self, source_service: str, target_service: str) -> tuple[bool, int, list[str]]:
        """
        Deterministic Python check:
        nx.has_path(graph, source=source_service, target=target_service)
        Note: service calls go target (consumer) -> source (dependency) OR source -> target depending on edge direction.
        In our topology:
        frontend -> recommendation (frontend calls recommendation)
        recommendation -> productcatalog
        checkout -> payment
        If payment breaks, affected is checkout. Path is checkout -> payment (or in reverse dependency: payment -> checkout).
        We check connectivity in undirected graph or directed dependency chain.
        """
        if source_service == target_service:
            return True, 0, [source_service]

        # Check topology subgraph of 'depends_on' edges
        topo = nx.DiGraph()
        for u, v, d in self.graph.edges(data=True):
            if d.get("type") == "depends_on":
                # u calls v, so an issue in v affects u.
                # Causal direction is v -> u (failure cascades from callee to caller)
                topo.add_edge(v, u)

        if topo.has_node(source_service) and topo.has_node(target_service):
            if nx.has_path(topo, source=source_service, target=target_service):
                path = nx.shortest_path(topo, source=source_service, target=target_service)
                hops = len(path) - 1
                return True, hops, path

        return False, 0, []

    def get_upstream_changes(self, service_id: str, window_minutes: int = 180, incident_id: str | None = None) -> list[Node]:
        """
        Hypothesis Agent tool:
        Traverses services that can causally affect service_id and gathers PRs/deploys within window.
        """
        # Find all services whose failures can cascade to service_id
        # In causal topo: callee -> caller, so candidates are ancestors in topo (or upstream dependencies)
        incident = self.get_incident_node(incident_id) if incident_id else None
        ref_time = incident.timestamp if incident and incident.timestamp else datetime.utcnow()

        start_time = ref_time - timedelta(minutes=window_minutes)
        end_time = ref_time + timedelta(minutes=10)

        # Build causal graph where v -> u means failure in v can affect u
        topo = nx.DiGraph()
        for u, v, d in self.graph.edges(data=True):
            if d.get("type") == "depends_on":
                topo.add_edge(v, u)

        relevant_services = {service_id}
        if topo.has_node(service_id):
            ancestors = nx.ancestors(topo, service_id)
            relevant_services.update(ancestors)

        candidate_nodes: list[Node] = []
        for node in self.nodes_dict.values():
            if node.type in ["pr", "deploy"] and node.service_id in relevant_services:
                if node.timestamp and start_time <= node.timestamp <= end_time:
                    candidate_nodes.append(node)

        candidate_nodes.sort(key=lambda n: n.timestamp or datetime.min, reverse=True)
        return candidate_nodes

    def find_coincident_deploys(self, incident_id: str, window_minutes: int = 30) -> list[Node]:
        """Challenger Agent tool: finds deploys occurring in the same window to test competing causes."""
        incident = self.get_incident_node(incident_id)
        if not incident or not incident.timestamp:
            return []

        start_time = incident.timestamp - timedelta(minutes=window_minutes)
        end_time = incident.timestamp + timedelta(minutes=5)

        deploys = []
        for node in self.nodes_dict.values():
            if node.type == "deploy" and node.timestamp:
                if start_time <= node.timestamp <= end_time:
                    deploys.append(node)
        return deploys

    def export_graph_for_ui(self, incident_id: str, chosen_cause_id: str | None = None, ruled_out_ids: dict[str, str] | None = None) -> dict:
        """
        Formats graph nodes and edges for React Flow UI with auto-layout styling.
        """
        ruled_out_ids = ruled_out_ids or {}
        incident = self.get_incident_node(incident_id)
        affected_service = incident.service_id if incident else None

        ui_nodes = []
        ui_edges = []

        subgraph_nodes = self.get_subgraph_around_incident(incident_id)
        included_node_ids = {n.id for n in subgraph_nodes}
        if chosen_cause_id and chosen_cause_id in self.nodes_dict:
            included_node_ids.add(chosen_cause_id)
        for r_id in ruled_out_ids:
            if r_id in self.nodes_dict:
                included_node_ids.add(r_id)

        for n_id in included_node_ids:
            node = self.nodes_dict[n_id]
            is_incident = (n_id == incident_id)
            is_chosen = (n_id == chosen_cause_id)
            is_ruled_out = n_id in ruled_out_ids
            is_superseded = bool(node.superseded_by)

            node_state = "normal"
            if is_incident:
                node_state = "incident"
            elif is_chosen:
                node_state = "chosen_cause"
            elif is_ruled_out:
                node_state = "ruled_out_candidate"
            elif is_superseded:
                node_state = "superseded_doc"

            ui_nodes.append({
                "id": node.id,
                "type": "custom",
                "data": {
                    "id": node.id,
                    "label": node.label,
                    "nodeType": node.type,
                    "state": node_state,
                    "timestamp": node.timestamp.isoformat() if node.timestamp else None,
                    "serviceId": node.service_id,
                    "sourceLink": node.source_link,
                    "supersededBy": node.superseded_by,
                    "ruledOutReason": ruled_out_ids.get(n_id),
                    "metadata": node.metadata,
                },
                "position": {"x": 0, "y": 0},
            })

        # Add edges between included nodes
        for edge in self.edges_list:
            if edge.source in included_node_ids and edge.target in included_node_ids:
                is_causal_path = False
                if chosen_cause_id and incident_id:
                    # Highlight edges connecting chosen cause to affected service
                    cause_node = self.nodes_dict.get(chosen_cause_id)
                    cause_svc = cause_node.service_id if cause_node else None
                    if (edge.source == chosen_cause_id) or (edge.source == cause_svc and edge.target == affected_service):
                        is_causal_path = True

                ui_edges.append({
                    "id": f"{edge.source}->{edge.target}",
                    "source": edge.source,
                    "target": edge.target,
                    "label": edge.type,
                    "data": {
                        "type": edge.type,
                        "evidence": edge.evidence,
                        "isCausalPath": is_causal_path,
                    },
                    "animated": is_causal_path,
                })

        return {"nodes": ui_nodes, "edges": ui_edges}


# Singleton engine instance
engine = CausalGraphEngine()
