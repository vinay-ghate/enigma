"""
API integration tests for Enigma endpoints.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app


@pytest.mark.asyncio
async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_list_incidents():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/incidents")
        assert res.status_code == 200
        incidents = res.json()
        assert len(incidents) == 5
        hero_count = sum(1 for i in incidents if i["is_hero"])
        assert hero_count == 3


@pytest.mark.asyncio
async def test_benchmarks_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/benchmarks")
        assert res.status_code == 200
        bench = res.json()
        assert "summary" in bench
        assert "incidents" in bench
        assert len(bench["incidents"]) == 5


@pytest.mark.asyncio
async def test_remediation_approval_workflow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/incidents/INC-101/approve",
            json={
                "approval_token": "APPROVE-ENIGMA-ROOTCAUSE",
                "reviewer": "test-judge@google.com",
                "action": "approve",
                "notes": "Verified causal path: PR #412 -> recommendationservice",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "approved"
        assert "pr_url" in data
        assert "audit_id" in data

        # Check audit log
        audit_res = await client.get("/api/audit-log")
        assert audit_res.status_code == 200
        logs = audit_res.json()
        assert len(logs) >= 1
        assert logs[-1]["incident_id"] == "INC-101"
