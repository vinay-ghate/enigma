# Enigma Testing & Evaluation Harness

## Evaluation Suite Overview
Enigma evaluates root-cause identification against 5 microservice incidents adapted from realistic production postmortems within the OpenTelemetry demo topology.

### The 5 Benchmark Scenarios
1. **INC-101 (Hero 1): Cache Stampede via TTL Reduction**
   - **Ground Truth Root Cause:** `PR #412` (recommendation cache TTL cut from 300s to 5s).
   - **Semantic Decoy:** `PR #409` (catalog cache TTL optimization, merged 3 days prior).
   - **Coincident Deploy:** `dep-ad-142` (adservice bump, 3m prior, no causal dependency path).
   - **Superseded Runbook:** `DOC-082` (caching guidelines superseded by PR #412).
2. **INC-102 (Hero 2): Cascading Checkout Outage (500s)**
   - **Ground Truth Root Cause:** `PR #521` (blocking 1500ms fraud check in paymentservice).
   - **Semantic Decoy:** `PR #518` (checkout button telemetry banner).
   - **Multi-hop Causal Path:** `paymentservice` -> `checkoutservice` -> `frontend` (2 hops).
3. **INC-103 (Hero 3): Cart CrashLoopBackOff & Stale Runbook Trap**
   - **Ground Truth Root Cause:** `PR #633` (redis connection pool reduced from 100 to 5).
   - **Superseded Runbook Decoy:** `RUNBOOK-CART-04` (recommends increasing memory to 512Mi, but cart migrated to external Redis pool via PR #590).
4. **INC-104 (Benchmark 4): Third-Party Gateway Provider Outage**
   - **Ground Truth Root Cause:** Major external fiber cut at third-party card provider (No internal PR bug).
   - **Semantic Decoy:** `PR #701` (payment retry policy merged 14 days ago).
   - **Expected Outcome:** Uncertain routing, automated code rollback blocked.
5. **INC-105 (Benchmark 5): Temporal Order Violation Trap**
   - **Ground Truth Root Cause:** `PR #815` (unindexed join query in productcatalogservice).
   - **Semantic Decoy:** `PR #820` (frontend promo banner merged 5m AFTER incident onset).
   - **Expected Outcome:** Challenger and Python Verifier reject PR #820 due to `cause.timestamp > incident.timestamp`.

## Running the Benchmark Evaluation
```powershell
.\.venv\Scripts\python -m pytest tests/
```
All 14 tests verify:
- Deterministic temporal checks (`cause.timestamp <= incident.timestamp`)
- NetworkX service dependency path hops
- Stale doc detection (`superseded_by is not None`)
- Adversarial falsification by the Challenger Agent
- Human approval gate & audit log immutability
- Unified SPA web serving
