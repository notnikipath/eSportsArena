from __future__ import annotations

import json
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path

DISCIPLINES = ["moba", "shooter", "strategy", "fighting", "sports_sim"]
METRICS = ["kills", "assists", "damage", "economy", "entry_success", "headshot_pct"]
PROVIDERS = ["hls", "webrtc", "twitch", "youtube"]
TEAMS = [
    "TEAM-ASTRA",
    "TEAM-NEON",
    "TEAM-NOVA",
    "TEAM-ECHO",
    "TEAM-ORBIT",
    "TEAM-SPARK",
]


def make_event(index: int) -> dict:
    team_a = random.choice(TEAMS)
    team_b = random.choice([item for item in TEAMS if item != team_a])
    actual_eta = random.uniform(20, 60)
    predicted_eta = actual_eta * random.uniform(0.92, 1.11)
    return {
        "arena_id": f"ARENA-{(index % 5) + 1:03d}",
        "match_id": f"MCH-{index:06d}",
        "discipline": random.choice(DISCIPLINES),
        "team_a": team_a,
        "team_b": team_b,
        "stream_provider": random.choice(PROVIDERS),
        "metric": random.choice(METRICS),
        "metric_value": round(random.uniform(3, 98), 2),
        "viewers": random.randint(2000, 150000),
        "stream_delay_sec": round(random.uniform(0.15, 11.8), 3),
        "actual_eta_min": round(actual_eta, 2),
        "predicted_eta_min": round(predicted_eta, 2),
        "cheat_score": round(random.uniform(0.2, 4.8), 3),
        "created_at": (datetime.now(UTC) - timedelta(seconds=index * 3)).isoformat(),
    }


if __name__ == "__main__":
    random.seed(42)
    output = Path(__file__).resolve().parents[1] / "data" / "samples" / "esports_events.json"
    payload = [make_event(i) for i in range(1, 12001)]
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(payload)} records to {output}")
