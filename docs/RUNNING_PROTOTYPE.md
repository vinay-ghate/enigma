# Enigma Prototype — Setup, Execution & Judge Guide

This guide walks you through setting up and running the Enigma Incident Root-Cause Investigation Prototype on Windows, Linux, or macOS.

---

## 1. Quick Prerequisites
- **Python 3.11+** (tested up to Python 3.14)
- **Node.js 18+** and `npm` (only needed if building or modifying the frontend)

---

## 2. Environment Setup

### Option A: Standard Python Virtual Environment

#### Windows (PowerShell)
```powershell
# 1. Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt
```

#### Linux / macOS (Bash / Zsh)
```bash
# 1. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt
```

---

## 3. Configuration (`.env`)

Enigma works **completely offline with zero API keys** out of the box using its pre-recorded replay engine. 

To configure live Gemini or GitHub integrations, copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

| Environment Variable | Required? | Default | Purpose |
| :--- | :--- | :--- | :--- |
| `GEMINI_API_KEY` | Optional | `""` | Powers live Gemini 2.5 Flash & Pro agent reasoning. |
| `GITHUB_TOKEN` | Optional | `""` | Scoped token to create draft PRs on sandbox repository. |
| `SANDBOX_REPO` | Optional | `enigma-sandbox/opentelemetry-demo` | Target GitHub repository for safe remediation. |
| `JUDGE_INVITE_CODE` | Optional | `ENIGMA-GCP-2026` | Judge access credential. |
| `DEFAULT_MODE` | Optional | `live` | Default execution mode (`live` or `replay`). |

---

## 4. Running the Prototype

### Method 1: Unified Single-Server Mode (Recommended for Judging)
The FastAPI backend serves both the REST/SSE APIs and the compiled React SPA from a single port:

```powershell
# Windows
.\.venv\Scripts\python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

# Linux / macOS
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser.

---

### Method 2: Development Mode (With Hot Reloading)

If you wish to modify backend agents or the React UI with hot-reloading:

#### Terminal 1 — Backend:
```powershell
.\.venv\Scripts\python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

#### Terminal 2 — Frontend:
```powershell
cd frontend
npm install
npm run dev
```
Open **[http://localhost:5173](http://localhost:5173)** in your browser (API requests automatically proxy to port 8000).

---

## 5. Running the Automated Evaluation Test Suite

To run all 14 unit and integration tests (deterministic verifier, agent loop, SSE streaming contract, approval workflow, and benchmarks):

```powershell
.\.venv\Scripts\python -m pytest tests/ -v
```

Expected output:
```text
tests/test_api.py::test_health PASSED
tests/test_api.py::test_list_incidents PASSED
tests/test_api.py::test_benchmarks_endpoint PASSED
tests/test_api.py::test_remediation_approval_workflow PASSED
tests/test_api.py::test_spa_serving PASSED
tests/test_pipeline.py::test_evidence_agent PASSED
tests/test_pipeline.py::test_naive_rag_baseline PASSED
tests/test_pipeline.py::test_hypothesis_and_challenger_loop PASSED
tests/test_pipeline.py::test_full_pipeline_stream PASSED
tests/test_verifier.py::test_topology_path_verification PASSED
tests/test_verifier.py::test_temporal_order_check PASSED
tests/test_verifier.py::test_superseded_doc_detection PASSED
tests/test_verifier.py::test_verifier_gates_valid_hypothesis PASSED
tests/test_verifier.py::test_verifier_rejects_temporal_violation PASSED

============================= 14 passed in 5.1s =============================
```

---

## 6. Judge 3-Minute Demo Walkthrough

Follow this step-by-step flow to evaluate Enigma against the PRD requirements:

1. **Select Incident 1 (`INC-101`)**:
   - Click **INC-101** (Hero: Recommendation Latency Spike).
   - Click **Investigate**.
2. **Observe Split-Screen Comparison**:
   - **Left Pane (Naive RAG Baseline)**: Notice standard vector search blamed `PR #409` due to keyword similarity ("cache TTL"), completely missing that PR #409 was merged 3 days prior without incident.
   - **Right Pane (Enigma Causal Output)**: Enigma identifies the true root cause: `PR #412` (Redis TTL reduced from 300s to 5s right before the alert).
3. **Inspect the Deterministic Verifier Badges**:
   - `Temporal Order`: Verified (merged 14m prior).
   - `Topology Path`: Verified (1 hop reachability in NetworkX graph).
   - `Stale Runbook`: Flagged (`DOC-082` superseded by `PR #412`).
4. **Explore the Interactive Graph**:
   - 🔴 **Red pulsing node**: Incident alert.
   - 🟢 **Emerald green node**: Verified root cause (`PR #412`).
   - ⚪ **Dashed grey/red pill**: Decoy `PR #409` marked with reason *"Ruled out as semantic trap"*.
   - 🟡 **Amber warning node**: Stale runbook `DOC-082` with *"Superseded by PR #412"* badge.
5. **Open the Live Turn-by-Turn Debate Drawer**:
   - Inspect the exchange between **Evidence Agent** (`Gemini 2.5 Flash`), **Hypothesis Agent** (`Gemini 2.5 Pro`), **Challenger Agent** (`Gemini 2.5 Pro`), and the **Deterministic Gate**.
   - Click source provenance links to verify cited PRs and logs.
6. **Trigger Human Approval & Remediation**:
   - Click **Review & Approve Remediation PR**.
   - Review Commit 1 (code rollback diff) and Commit 2 (superseded runbook modernization patch).
   - Click **Approve & Create Draft PR** to simulate safe draft creation and audit logging.
7. **Review Benchmarks**:
   - Click **Benchmarks (5/5)** in the top navigation bar to view the measured evaluation matrix across all 5 incident scenarios.
