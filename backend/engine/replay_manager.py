"""
Replay Manager for Enigma.
Loads and saves pre-recorded investigation runs and SSE streams.
Enforces Core Architecture Rule #5 (Replay First).
"""

from __future__ import annotations
import json
import asyncio
from pathlib import Path
from typing import AsyncGenerator
from backend.models.schema import IncidentSummary
from backend.data.loader import load_incidents
from backend.agents.pipeline import pipeline

REPLAYS_DIR = Path(__file__).resolve().parent.parent.parent / "seed_data" / "replays"
REPLAYS_DIR.mkdir(parents=True, exist_ok=True)


async def generate_and_save_replays():
    """Generates and persists replay recordings for all seeded incidents."""
    incidents = load_incidents()
    for inc in incidents:
        events = []
        async for sse_chunk in pipeline.run_investigation_stream(inc.id, mode="replay"):
            events.append(sse_chunk)

        replay_file = REPLAYS_DIR / f"{inc.id}.json"
        with open(replay_file, "w", encoding="utf-8") as f:
            json.dump({"incident_id": inc.id, "events": events}, f, indent=2)


def get_replay_events(incident_id: str) -> list[str] | None:
    replay_file = REPLAYS_DIR / f"{incident_id}.json"
    if not replay_file.exists():
        return None
    with open(replay_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("events", [])


async def stream_replay(incident_id: str) -> AsyncGenerator[str, None]:
    events = get_replay_events(incident_id)
    if not events:
        # Fallback to live stream generator
        async for chunk in pipeline.run_investigation_stream(incident_id, mode="replay"):
            yield chunk
        return

    for event_str in events:
        yield event_str
        await asyncio.sleep(0.35)
