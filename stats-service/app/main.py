from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import UTC, datetime
from statistics import mean
from typing import Any
from uuid import uuid4

from fastapi import FastAPI
from pydantic import BaseModel, Field

from shared.esports_common import (
    MatchStatsEvent,
    Settings,
    TTLCache,
    availability_pct,
    calculate_mape,
    detect_cheat_risk,
    is_cheat_suspected,
    predict_win_probability,
    stats_refresh_ms,
)

settings = Settings(service_name="stats-service", service_port=8604)
app = FastAPI(title="eSports Arena Stats Service", version="1.0.0")

stats_events: list[MatchStatsEvent] = []
cheat_alerts: list[dict[str, Any]] = []

kpi_cache = TTLCache(ttl_seconds=15)
availability_minutes: dict[str, tuple[int, int]] = {"ARENA-DEMO": (43160, 43200)}


class CollectStartRequest(BaseModel):
    match_id: str


class MapeRequest(BaseModel):
    actual: list[float] = Field(default_factory=list)
    predicted: list[float] = Field(default_factory=list)


class OutcomePredictRequest(BaseModel):
    team_a_rating: int
    team_b_rating: int
    recent_form_delta: float = 0


class CheatDetectRequest(BaseModel):
    match_id: str
    metric: str
    values: list[float] = Field(default_factory=list)
    threshold: float = 3.2


CollectStartRequest.model_rebuild()
MapeRequest.model_rebuild()
OutcomePredictRequest.model_rebuild()
CheatDetectRequest.model_rebuild()


async def _collect_stats(match_id: str) -> None:
    metric_plan = [
        ("kills_team_a", 14),
        ("kills_team_b", 11),
        ("economy_team_a", 82),
        ("economy_team_b", 79),
        ("entry_success_team_a", 61),
    ]
    for metric, value in metric_plan:
        await asyncio.sleep(0.02)
        stats_events.append(
            MatchStatsEvent(
                event_id=str(uuid4()),
                match_id=match_id,
                metric=metric,
                value=float(value),
                source="async_collector",
            )
        )
    kpi_cache.set("kpi:ARENA-DEMO", None)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.post("/stats/events")
async def ingest_event(event: MatchStatsEvent) -> dict[str, Any]:
    stats_events.append(event)
    return {"status": "accepted", "event_id": event.event_id}


@app.post("/stats/collect/start")
async def start_collect(request: CollectStartRequest) -> dict[str, Any]:
    job_id = f"JOB-{uuid4().hex[:10].upper()}"
    asyncio.create_task(_collect_stats(request.match_id))
    return {"status": "started", "job_id": job_id, "match_id": request.match_id}


@app.get("/stats/match/{match_id}")
async def match_stats(match_id: str) -> dict[str, Any]:
    items = [event.model_dump(mode="json") for event in stats_events if event.match_id == match_id]
    refresh = stats_refresh_ms(len(items), workers=12)
    return {"items": items, "count": len(items), "refresh_ms": refresh}


@app.post("/stats/eta/mape")
async def eta_mape(request: MapeRequest) -> dict[str, Any]:
    mape = calculate_mape(request.actual, request.predicted)
    return {
        "mape_pct": mape,
        "target_pct": settings.eta_mape_target_pct,
        "within_target": mape <= settings.eta_mape_target_pct,
    }


@app.post("/stats/predict/outcome")
async def predict_outcome(request: OutcomePredictRequest) -> dict[str, Any]:
    probability = predict_win_probability(
        team_a_rating=request.team_a_rating,
        team_b_rating=request.team_b_rating,
        recent_form_delta=request.recent_form_delta,
    )
    return {"team_a_win_probability": probability, "team_b_win_probability": round(1 - probability, 4)}


@app.post("/stats/cheat/detect")
async def detect_cheat(request: CheatDetectRequest) -> dict[str, Any]:
    score = detect_cheat_risk(request.values)
    suspected = is_cheat_suspected(request.values, threshold=request.threshold)
    alert = None
    if suspected:
        alert = {
            "alert_id": str(uuid4()),
            "match_id": request.match_id,
            "metric": request.metric,
            "score": score,
            "threshold": request.threshold,
            "severity": "critical",
            "created_at": datetime.now(UTC).isoformat(),
        }
        cheat_alerts.append(alert)
    return {"suspected": suspected, "score": score, "alert": alert}


@app.get("/stats/anomalies")
async def anomalies(match_id: str | None = None) -> dict[str, Any]:
    items = [item for item in cheat_alerts if not match_id or item["match_id"] == match_id]
    return {"items": items, "count": len(items)}


@app.get("/stats/kpi")
async def kpi(arena_id: str = "ARENA-DEMO") -> dict[str, Any]:
    cache_key = f"kpi:{arena_id}"
    cached = kpi_cache.get(cache_key)
    if cached:
        return {**cached, "cached": True}

    arena_events = [event for event in stats_events if event.match_id.startswith("MCH")]
    refresh_ms = stats_refresh_ms(len(arena_events), workers=12)
    avg_delay = 8.2
    uptime, total = availability_minutes.get(arena_id, (43100, 43200))

    payload = {
        "stream_delay_sec": avg_delay,
        "target_stream_delay_sec": settings.stream_delay_target_sec,
        "stats_refresh_sec": round(refresh_ms / 1000, 3),
        "target_stats_refresh_sec": settings.stats_refresh_target_sec,
        "availability_pct": availability_pct(uptime, total),
        "viewer_capacity_target": settings.viewer_capacity_target,
        "events_count": len(arena_events),
        "cheat_alerts": len(cheat_alerts),
        "eta_mape_target_pct": settings.eta_mape_target_pct,
        "cached": False,
    }
    kpi_cache.set(cache_key, payload)
    return payload
