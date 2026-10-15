# Enigma: Product Requirements Document (Prototype)

*Incident root-cause investigation with agents and a causal graph. Google Cloud hackathon prototype. Team Enigma. Status: Draft v0.2*

## 1. Overview

**Enigma** investigates production incidents and explains what actually caused them. Standard RAG finds documents that *sound* related to an incident. Enigma builds a timeline of changes, links them in a cause-effect graph, has one agent propose a root cause and another try to disprove it, and then drafts a fix for human approval.

**One-line pitch:** From "what looks relevant" to "what actually caused this, and what to do next."

**Hackathon track fit:** Enterprise knowledge assistant, intelligent search, and workflow automation. It improves knowledge accessibility (finding the real cause across PRs, tickets, chat, and docs) and workflow execution (draft remediation with approval).

## 2. Problem

| Problem | Effect |
| --- | --- |
| Semantic search returns text-similar but causally unrelated PRs and docs (the "semantic trap") | Wrong fixes, wasted triage time |
| Documentation goes stale after later changes | Teams follow outdated runbooks |
| Evidence is scattered across GitHub, Jira, Slack, and logs | Slow, manual incident investigation |
| LLM answers sound confident without showing evidence | Low trust, no audit trail |

## 3. Goals and Non-goals

### Goals (prototype)

1. Diagnose seeded incidents with higher root-cause accuracy than a naive RAG baseline.
2. Show the reasoning: timeline, hypotheses, challenges, evidence for and against, and unresolved gaps.
3. Detect and visibly flag one superseded document.
4. Draft a remediation PR on a sandbox repo behind a human approval step.
5. Provide a hosted demo judges can try, with a replay fallback.
6. Report measured results only (accuracy, wrong-fix rate, cost, time).

### Non-goals (prototype)

- Real production writes or real customer data.
- Live Jira and Slack integrations (seeded exports instead).
- Full multi-tenant access control, SSO, or billing.
- Proof of causation. Enigma produces evidence-ranked hypotheses, not formal causal proof.
- Delta graph processing and context caching (roadmap only).

## 4. Users and Use Cases

| User | Need |
| --- | --- |
| On-call engineer | Fast, evidence-backed root cause during an incident |
| Engineering manager | Incident report with timeline, confidence, and ownership of the change |
| Hackathon judge | Try incidents, see the reasoning, compare against naive RAG |

**Primary use case:** A latency or error alert fires. The user selects the incident and gets a ranked root cause, supporting and contradicting evidence, a proposed fix PR, and a list of stale docs.

## 5. Pipeline and Naming

Enigma uses a 4-stage pipeline.

| Stage | Job | Prototype implementation |
| --- | --- | --- |
| **Ingest** | Pull and normalize PRs, deploys, tickets, chat, metrics into events | GitHub API for PRs and commits on the sandbox fork. Seeded JSON for Jira and Slack. Saved metrics snapshots. Service topology is seeded deterministically from the demo's architecture and config. Gemini Flash only maps events (PRs, tickets, chat) onto existing service nodes and links docs (supersedes). |
| **Memory** | Store events, docs, links, and validity | Seeded graph loaded into memory (NetworkX) at API startup. Firestore: runs, audit log, and replays. Vertex AI Search index for runbooks and design docs. |
| **Analyze** | Build the cause-effect graph, generate and test hypotheses | Graph traversal in app code, deterministic hard checks, Gemini Pro for hypothesis scoring |
| **Act** | Draft remediation and require approval | Draft revert PR with a rich body (causal path, evidence links) on the sandbox repo, approval button, audit log |

## 6. Agent Design (ADK)

```text
Incident -> Evidence Agent -> Hypothesis Agent <-> Challenger Agent -> Evidence Review -> Remediation Agent -> Human Approval
```

| Agent | Responsibility | Model |
| --- | --- | --- |
| Evidence Agent | Gathers events around the incident window and builds the timeline. States what is known, does not speculate. | Flash |
| Hypothesis Agent | Proposes "change X caused symptom Y" with the expected causal path and cited evidence. Tool: upstream changes along the failing service's dependency path | Pro |
| Challenger Agent | Tries to disprove it: timing, dependency path, competing deploys, historical incidents. States what evidence would falsify the claim. Tools (distinct from the Hypothesis Agent): sibling and unrelated deploys in the same window, historical false positives, timestamp order checks. | Pro |
| Remediation Agent | Drafts revert or fix PR, incident report, and runbook update flags. Never executes without approval. | Pro |

**Loop rule:** Hypothesis and Challenger iterate up to N rounds (default 1 for live demos, configurable to 2). The output is a ranked list of hypotheses with confidence, evidence for, evidence against, and unresolved gaps.

**Confidence rule:** Model confidence is a routing signal, not a calibrated probability. The Remediation Agent only drafts a fix when the top hypothesis passes hard checks: change precedes the incident, a dependency path exists from the changed component to the affected service, and no competing hypothesis is better supported. Each check is computed in code, not by the LLM, and shown in the UI as a badge (for example temporal order verified, dependency path of 2 hops). Otherwise the output is "uncertain, more evidence needed."

## 7. Functional Requirements

### P0 (must have)

| ID | Requirement |
| --- | --- |
| F1 | Incident picker with 3 hero incidents, each runnable with one click (5 incidents total in the benchmark suite) |
| F2 | Ingest seeded PRs, deploys, tickets, chat, and metric snapshots into Memory as nodes and edges |
| F3 | Evidence Agent produces a time-ordered timeline for the selected incident |
| F4 | Hypothesis and Challenger agents run and stream their exchange to the UI live |
| F5 | Output includes ranked hypotheses, evidence cards (supporting and contradicting), unresolved gaps, and a "what would falsify this" note |
| F6 | Interactive graph view with the chosen cause highlighted and ruled-out candidates marked with a reason (node colors: incident red, chosen cause green, ruled-out grey, stale doc amber) |
| F7 | **Naive RAG baseline** (Vertex AI Search plus Gemini) on the same incident, shown side by side with Enigma, with the decoy PR highlighted on the Enigma graph and the reason it was ruled out (trap visualizer) |
| F8 | Every claim links back to its source record (PR, ticket, message, log) |
| F9 | Approval button creates a draft PR on the sandbox repo with a rich body (causal path, evidence links, why the decoy was ruled out) and shows its link |
| F10 | Replay mode serving cached runs when live calls fail, clearly labeled "replay" |
| F20 | Deterministic hard-check badges in the UI (temporal order verified, dependency path hops, stale doc flagged), computed in code and not by the LLM |

### P1 (should have)

| ID | Requirement |
| --- | --- |
| F11 | Superseded-doc detection with a visible "superseded by PR #X" badge |
| F12 | Benchmark page: Enigma vs naive RAG across all seeded incidents |
| F13 | Flash vs Pro routing, with token and cost shown per investigation |
| F14 | Single shared judge invite code and a global concurrency limit (no per-user login) |
| F15 | Audit log of hypotheses, approvals, and actions |
| F21 | Second commit in the draft PR that updates the superseded runbook |

### P2 (stretch)

| ID | Requirement |
| --- | --- |
| F17 | Deploy agents on Vertex AI Agent Engine |
| F18 | Read-only "bring your own public repo" mode |
| F19 | Cloud Logging as a live signal source for one service |

## 8. Demo Dataset

**Target app:** a fork of the OpenTelemetry demo (`enigma-sandbox`), using 3 to 4 services (frontend, cart, recommendation, product catalog) and its failure-injection feature flags. Verify current flag and service names in the repo before building.

**Seed data:** about 30 to 50 PRs, about 20 Jira tickets, a Slack export, 3 to 5 docs and runbooks, and **5 incidents with known ground-truth root causes** (some adapted from public postmortems).

**Required traps in the dataset**

| Trap | Purpose |
| --- | --- |
| Semantically similar PR on a different service | Fools naive RAG |
| Coincident unrelated deploy shortly before the incident | Tests the Challenger |
| Superseded design doc or runbook | Tests stale-knowledge detection |
| One genuinely ambiguous incident | Shows honest "uncertain" output |
| Cascading dependency failure across services | Tests multi-hop dependency paths |

**Example incident:** Recommendation latency rises and checkout slows. Ground truth: a cache TTL change PR. Decoy: a catalog caching refactor with similar wording. Coincident: an unrelated ad service deploy minutes earlier. Stale doc: a runbook stating the old TTL.

## 9. User Experience

| Screen | Content |
| --- | --- |
| Home / incident picker | Incident cards with symptom and time. "Run Enigma" button. |
| Compare view | Naive RAG answer vs Enigma answer, side by side, with the decoy highlighted on the graph |
| Investigation view | Timeline, live agent exchange, graph, evidence cards |
| Action view | Proposed fix diff, approve or reject, draft PR link |
| Benchmarks | Accuracy, wrong-fix rate, cost, and time tables |

**Demo flow (3 minutes):** alert, naive RAG gets it wrong, Enigma investigates live, graph shows the trap ruled out, stale doc badge, approve and open the draft PR, benchmark slide.

## 10. Architecture and Stack

| Area | Choice |
| --- | --- |
| Language / backend | Python, FastAPI, Pydantic, NetworkX for graph traversal |
| Agents | Google ADK |
| Models | Gemini Flash and Pro on Vertex AI with Pydantic structured output (confirm current model names and quota before building) |
| Retrieval baseline | Vertex AI Search |
| Storage | Firestore (runs, audit log, replays), Cloud Storage (seed data). The seeded graph is held in memory (NetworkX) at API startup. |
| Frontend | React with React Flow (dagre auto-layout). Streaming via SSE. |
| Hosting | Cloud Run (API and frontend), Secret Manager, Cloud Build |
| External | GitHub REST API (sandbox repo only) |
| Optional | Pub/Sub, Document AI, BigQuery (benchmarks), Agent Engine, Cloud Logging |

**Key data model**

| Entity | Fields |
| --- | --- |
| Node | id, type (pr, deploy, ticket, message, doc, service, incident), timestamp, source link, validity interval, superseded\_by |
| Edge | from, to, type (modifies, depends\_on, caused\_by\_candidate, supersedes, discussed\_in), evidence |
| Hypothesis | incident, cause node, confidence, supporting, contradicting, gaps, falsifiers |
| Run | incident, agent messages, outputs, tokens, cost, latency, mode (live or replay) |

## 11. Hosting and Access

| Item | Requirement |
| --- | --- |
| Default mode | Guided scenarios running live agents on saved incident snapshots |
| Fallback | Replay mode with cached runs |
| Access | Single shared judge invite code |
| Cost control | Global concurrency limit, cap on Pro calls, budget alert |
| Safety | Sandbox repo only. No real production writes. Retrieved content treated as untrusted data, never as instructions. |

## 12. Success Metrics

Report only measured values from a defined evaluation set. With 5 incidents the set is small, so label it that way and show per-incident results, not only percentages.

| Metric | Naive RAG | Enigma | Target |
| --- | --- | --- | --- |
| Root-cause accuracy (top-1) | measure | measure | Enigma clearly higher |
| Wrong-fix / false attribution rate | measure | measure | Enigma lower |
| Tokens and cost per investigation | measure | measure | Report both honestly |
| Time to diagnosis | measure | measure | Report both honestly |
| Stale-doc detection | measure | measure | Detects seeded cases |
| Hosted demo uptime during judging | n/a | n/a | No failed demo runs |

## 13. Security and Governance

- Least-privilege tokens, with the GitHub token scoped to the sandbox repo only.
- Human approval required for any action.
- Provenance links on every finding.
- Prompt-injection resistance: PR text, tickets, and chat are data, not instructions.
- Audit log of hypotheses, approvals, and actions.
- Findings separate confirmed facts, supported hypotheses, and unresolved questions.

## 14. Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| Scope creep | Build one vertical slice. Keep P2 items out until P0 is done. |
| LLM causal claims overstated | Challenger agent, hard checks, visible gaps section |
| Live demo or quota failure | Replay mode and a recorded video |
| Weak or strawman baseline | Build the naive RAG baseline with real effort |
| Pro model quota or cost | Check quota early, route to Flash where possible, cap calls |
| Synthetic data looks fake | Use a real app fork, real PR history, and incidents adapted from public postmortems |
| LLM builds wrong dependency or causal edges | Seed service topology deterministically. Use Flash only to map events onto existing service nodes. |
| End-to-end run takes 45 to 90 seconds | Stream each agent step over SSE and default to 1 Challenger round in live demos. |

## 15. Milestones

| Phase | Output |
| --- | --- |
| 1. Data and baseline | Sandbox fork, seeded incidents with ground truth, naive RAG baseline |
| 2. Memory and agents | Graph in Firestore, ADK agents producing timeline and ranked hypotheses |
| 3. Action and UI | Approval flow, draft PR, graph and agent exchange UI, compare view |
| 4. Benchmark and hosting | Run comparison, deploy to Cloud Run, add replay mode |
| 5. Polish | 3-minute video, README, architecture diagram, cost notes |

Reserve the last 20 to 25 percent of the schedule for phases 4 and 5.

## 16. Open Questions

1. Submission deadline and team size, to turn the phases into dated tasks.
2. GCP project, credits, and Gemini Pro quota status.
3. Final 3 hero incidents and 5 total, with the trap for each.
4. Which Gemini Flash and Pro model names and quotas are available in the GCP project.
5. Whether to deploy on Agent Engine, only if it is a one-command push from the ADK setup.
