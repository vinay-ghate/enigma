# enigma-sandbox: Clone, Run, Use

Repo: https://github.com/vinay-ghate/enigma-sandbox
Upstream: open-telemetry/opentelemetry-demo (the "Astronomy Shop" microservice app)
Purpose: the sandbox app that Enigma investigates. It supplies real PRs, failure-injection flags, and a place for draft PRs.

Commands below are for Windows PowerShell. Ports, URLs, and file paths are from memory of the upstream demo, so verify them against the repo's README and docs.

## 1. Prerequisites

| Tool | Check |
|---|---|
| Git | `git --version` |
| Docker Desktop (Linux containers, WSL 2 backend) | `docker info` prints a Server section |
| RAM | Several GB free for Docker. The full stack is heavy. |
| (Later) Python 3.11+ and Node.js | For the Enigma backend and frontend |

## 2. Clone

```powershell
cd D:\Programming\GitRepos
git clone https://github.com/vinay-ghate/enigma-sandbox.git
cd enigma-sandbox
```

Optional, so you can pull upstream changes:

```powershell
git remote add upstream https://github.com/open-telemetry/opentelemetry-demo.git
git fetch upstream
```

## 3. Run

Start light first (core services only):

```powershell
docker compose up --detach
```

The first run pulls many images from ghcr.io and takes a while.

Check status:

```powershell
docker compose ps
```

Full stack with observability and extras (needs more RAM):

```powershell
docker compose --env-file .env --env-file .env.override -f compose.yaml -f compose.observability.yaml -f compose.extras.yaml up --force-recreate --remove-orphans --detach
```

Stop:

```powershell
docker compose down
```

## 4. Open the app

Verify the current port and paths in the README and docs.

| What | Usual address |
|---|---|
| Web store | http://localhost:8080 |
| Feature flag UI | http://localhost:8080/feature |
| Load generator | http://localhost:8080/loadgenerator |
| Grafana | http://localhost:8080/grafana |
| Jaeger | http://localhost:8080/jaeger/ui |

Confirm the load generator is producing traffic before you inject a failure.

## 5. Use it for Enigma

1. Find the feature flag config (usually under `src/flagd/`) and list the available failure flags.
2. Pick 3 to 4 flags for the hero incidents.
3. For each planned incident, create real PRs in this fork:
   - the true cause (flag or config change)
   - a decoy (similar wording, different service)
   - a coincident unrelated change merged shortly before the spike
4. Record each merge timestamp.
5. Flip the flag, wait for the spike, then export a metrics and trace snapshot to JSON or CSV.
6. Export PR and commit data through the GitHub API into the Enigma seed folder, so the hosted demo runs without the live stack.
7. Write the ground-truth file per incident: true cause, decoy, coincident deploy, superseded doc.

## 6. Keys and secrets

Do not put secrets in `.env` or `.env.override`. Those are tracked files from the upstream demo.

Keep Enigma's keys in a separate, git-ignored file (for example `.env.enigma`) and add it to `.gitignore`.

| Key | When |
|---|---|
| `GOOGLE_API_KEY` | Local prototype (Gemini via AI Studio) |
| `GITHUB_TOKEN` | Fine-grained token limited to `enigma-sandbox`, needed for the draft PR step |
| `GITHUB_REPO` | `vinay-ghate/enigma-sandbox` |

Vertex AI, Firestore, and invite-code settings come later, at deployment.

## 7. Troubleshooting

| Error | Fix |
|---|---|
| `open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified` | Start Docker Desktop, wait for "Engine running", confirm Linux containers mode, check `docker context ls` shows `desktop-linux`, and run `wsl --update` then `wsl --shutdown` if needed |
| Image pull fails or is very slow | Retry, check network access to ghcr.io, and start with the light stack |
| Containers restart or exit | Raise Docker Desktop memory, or run fewer services |
| Port already in use | Stop the other process or change the port in `.env` |

## 8. Current state of the repo

As of the last check, this repo is the unmodified upstream demo. It has no Enigma app code, no seeded incidents, and no sandbox PR history yet. Enigma's backend and frontend can live in a separate repo or in a new top-level folder here.