"""
Data Loader for Enigma Causal Memory.
Loads seed datasets into canonical Node and Edge models.
"""

from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime
from backend.models.schema import Node, Edge, IncidentSummary

SEED_DIR = Path(__file__).resolve().parent.parent.parent / "seed_data"


def parse_dt(val: str | None) -> datetime | None:
    if not val:
        return None
    # normalize ISO format ending with Z
    return datetime.fromisoformat(val.replace("Z", "+00:00"))


def load_incidents() -> list[IncidentSummary]:
    incidents_path = SEED_DIR / "incidents.json"
    with open(incidents_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [
        IncidentSummary(
            id=item["id"],
            title=item["title"],
            service_id=item["service_id"],
            severity=item["severity"],
            timestamp=parse_dt(item["timestamp"]),
            description=item["description"],
            ground_truth_cause=item["ground_truth_cause"],
            trap_type=item["trap_type"],
            decoy_node_id=item["decoy_node_id"],
        )
        for item in data
    ]


def load_nodes_and_edges() -> tuple[list[Node], list[Edge]]:
    nodes: list[Node] = []
    edges: list[Edge] = []

    # 1. Services & Topology
    with open(SEED_DIR / "topology.json", "r", encoding="utf-8") as f:
        top_data = json.load(f)

    for svc in top_data.get("services", []):
        nodes.append(
            Node(
                id=svc["id"],
                type="service",
                label=svc["name"],
                service_id=svc["id"],
                metadata={"tier": svc.get("tier"), "language": svc.get("language"), "desc": svc.get("description")},
            )
        )

    for dep in top_data.get("dependencies", []):
        edges.append(
            Edge(
                source=dep["source"],
                target=dep["target"],
                type=dep["type"],
                evidence=dep.get("evidence", ""),
            )
        )

    # 2. PRs
    with open(SEED_DIR / "prs.json", "r", encoding="utf-8") as f:
        prs_data = json.load(f)

    for pr in prs_data:
        t = parse_dt(pr["merged_at"]) or parse_dt(pr["timestamp"])
        nodes.append(
            Node(
                id=pr["id"],
                type="pr",
                label=f"PR #{pr['number']}: {pr['title']}",
                timestamp=t,
                service_id=pr["service_id"],
                source_link=pr["source_link"],
                metadata={
                    "number": pr["number"],
                    "branch": pr.get("branch"),
                    "diff": pr.get("diff"),
                    "description": pr.get("description"),
                    "author": pr.get("author"),
                },
            )
        )
        # Deterministic edge: PR modifies Service
        edges.append(
            Edge(
                source=pr["id"],
                target=pr["service_id"],
                type="modifies",
                evidence=f"GitHub PR #{pr['number']} merged into {pr['service_id']}",
            )
        )

    # 3. Deploys
    with open(SEED_DIR / "deploys.json", "r", encoding="utf-8") as f:
        dep_data = json.load(f)

    for d in dep_data:
        t = parse_dt(d["timestamp"])
        nodes.append(
            Node(
                id=d["id"],
                type="deploy",
                label=f"Deploy: {d['image_tag']}",
                timestamp=t,
                service_id=d["service_id"],
                source_link="",
                metadata={
                    "image_tag": d["image_tag"],
                    "environment": d.get("environment"),
                    "status": d.get("status"),
                    "description": d.get("description"),
                },
            )
        )
        edges.append(
            Edge(
                source=d["id"],
                target=d["service_id"],
                type="modifies",
                evidence=f"Deployment artifact {d['image_tag']} released to {d['service_id']}",
            )
        )

    # 4. Jira Tickets
    with open(SEED_DIR / "tickets.json", "r", encoding="utf-8") as f:
        tickets_data = json.load(f)

    for tick in tickets_data:
        t = parse_dt(tick["created_at"])
        nodes.append(
            Node(
                id=tick["id"],
                type="ticket",
                label=f"{tick['key']}: {tick['title']}",
                timestamp=t,
                service_id=tick["service_id"],
                source_link=tick["source_link"],
                metadata={
                    "key": tick["key"],
                    "status": tick["status"],
                    "description": tick.get("description"),
                },
            )
        )
        if tick.get("linked_pr"):
            edges.append(
                Edge(
                    source=tick["id"],
                    target=tick["linked_pr"],
                    type="discussed_in",
                    evidence=f"Jira issue {tick['key']} tracked implementation of {tick['linked_pr']}",
                )
            )

    # 5. Slack Messages
    with open(SEED_DIR / "slack.json", "r", encoding="utf-8") as f:
        slack_data = json.load(f)

    for msg in slack_data:
        t = parse_dt(msg["timestamp"])
        nodes.append(
            Node(
                id=msg["id"],
                type="message",
                label=f"Slack ({msg['channel']}): {msg['text'][:40]}...",
                timestamp=t,
                source_link=msg["source_link"],
                metadata={"user": msg["user"], "channel": msg["channel"], "text": msg["text"]},
            )
        )

    # 6. Runbooks / Docs
    with open(SEED_DIR / "runbooks.json", "r", encoding="utf-8") as f:
        docs_data = json.load(f)

    for doc in docs_data:
        t = parse_dt(doc["last_updated"])
        nodes.append(
            Node(
                id=doc["id"],
                type="doc",
                label=doc["title"],
                timestamp=t,
                service_id=doc.get("service_id"),
                source_link=doc["source_link"],
                superseded_by=doc.get("superseded_by"),
                metadata={"content": doc["content"], "is_stale": doc.get("is_stale", False)},
            )
        )
        if doc.get("superseded_by"):
            edges.append(
                Edge(
                    source=doc["superseded_by"],
                    target=doc["id"],
                    type="supersedes",
                    evidence=f"{doc['superseded_by']} altered configuration documented in {doc['id']}",
                )
            )

    # 7. Incidents
    incidents = load_incidents()
    for inc in incidents:
        nodes.append(
            Node(
                id=inc.id,
                type="incident",
                label=f"Incident {inc.id}: {inc.title}",
                timestamp=inc.timestamp,
                service_id=inc.service_id,
                metadata={
                    "severity": inc.severity,
                    "description": inc.description,
                    "ground_truth_cause": inc.ground_truth_cause,
                    "trap_type": inc.trap_type,
                    "decoy_node_id": inc.decoy_node_id,
                },
            )
        )

    return nodes, edges
