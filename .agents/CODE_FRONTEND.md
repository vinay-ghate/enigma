# Frontend Coding Agent Guidelines

## Stack & Conventions
- React 19, TypeScript, Vite, Tailwind CSS, `shadcn/ui`, `@xyflow/react` (React Flow), `dagre`, `lucide-react`[cite: 1].
- Dark-mode engineering aesthetic (slate-950 backgrounds, high-contrast status badges).

## Required Views & Components
1. **Incident Picker & Header:**
   - 1-click incident scenario cards + global toggle for `Live ADK Run` vs `Cached Replay`[cite: 1].
2. **Compare View (Split Screen):**
   - Left pane: **Naive RAG Baseline** (shows the semantic trap / wrong PR picked by standard vector search)[cite: 1].
   - Right pane: **Enigma Causal Output** (shows true root cause, deterministic verification badges, and why the decoy PR was ruled out)[cite: 1].
3. **Interactive Causal Graph (`CausalGraph.tsx`):**
   - Use `dagre` to auto-layout nodes left-to-right by timestamp/dependency.
   - Node styling rules:
     - `incident`: Pulsing red border.
     - `chosen_cause`: Solid emerald green border + `[Root Cause]` badge[cite: 1].
     - `ruled_out_candidate`: Muted grey/red dashed border with a visible pill showing `ruled_out_reason` (e.g., *"Deployed 4m after alert"* or *"No dependency path"*)[cite: 1].
     - `superseded_doc`: Amber warning border with `"Superseded by PR #X"` badge[cite: 1].
4. **Live Agent Debate Drawer:**
   - Consumes SSE `agent_message` events. Clearly distinguishes `Evidence (Flash)`, `Hypothesis (Pro)`, and `Challenger (Pro)` with expandable source provenance links (`source_link`) on every claim[cite: 1].
5. **Action & Approval Modal:**
   - Displays git diff preview and `[Approve & Create Draft PR]` button[cite: 1]. Once clicked, renders the live GitHub PR URL and logs to the audit table[cite: 1].