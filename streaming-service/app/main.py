from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException

from shared.esports_common import (
    IntegrationSyncRequest,
    IntegrationSyncResult,
    Role,
    Settings,
    StreamCreateRequest,
    StreamSession,
    estimate_stream_delay_sec,
    has_permission,
)

settings = Settings(service_name="streaming-service", service_port=8607)
app = FastAPI(title="eSports Arena Streaming Service", version="1.0.0")

streams: dict[str, StreamSession] = {}
history: list[IntegrationSyncResult] = []

video_nodes = [
    {"node": "rtmp-eu-1", "capacity": 50000, "active_viewers": 18000},
    {"node": "rtmp-eu-2", "capacity": 50000, "active_viewers": 14000},
    {"node": "rtmp-ru-1", "capacity": 40000, "active_viewers": 11000},
]


def _assert_manage(role: Role) -> None:
    if not has_permission(role, "stream:manage"):
        raise HTTPException(status_code=403, detail="Forbidden")


def _pick_node() -> dict[str, Any]:
    return sorted(video_nodes, key=lambda item: item["active_viewers"] / item["capacity"])[0]


def _push(system_name: str, details: dict[str, Any]) -> dict[str, Any]:
    event = IntegrationSyncResult(sync_id=str(uuid4()), system_name=system_name, status="ok", details=details)
    history.append(event)
    return event.model_dump(mode="json")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.post("/streams/create")
async def create_stream(request: StreamCreateRequest) -> dict[str, Any]:
    _assert_manage(request.actor_role)
    node = _pick_node()
    projected_viewers = node["active_viewers"] + 12000
    node["active_viewers"] = projected_viewers

    delay_sec = estimate_stream_delay_sec(request.provider, viewers=projected_viewers, balanced=True)
    stream = StreamSession(
        stream_id=f"STR-{uuid4().hex[:10].upper()}",
        match_id=request.match_id,
        provider=request.provider,
        stream_url=f"https://stream.arena.local/watch/{request.match_id.lower()}",
        ingest_url=f"rtmp://{node['node']}/live/{request.match_id.lower()}",
        delay_sec=delay_sec,
    )
    streams[stream.stream_id] = stream
    return {
        **stream.model_dump(mode="json"),
        "node": node["node"],
        "balanced": True,
    }


@app.get("/streams")
async def list_streams(match_id: str | None = None) -> dict[str, Any]:
    items = [item.model_dump(mode="json") for item in streams.values() if not match_id or item.match_id == match_id]
    return {"items": items, "count": len(items)}


@app.get("/streams/nodes")
async def list_nodes() -> dict[str, Any]:
    return {"items": video_nodes, "count": len(video_nodes)}


@app.post("/integrations/twitch/connect")
async def connect_twitch(request: IntegrationSyncRequest) -> dict[str, Any]:
    _assert_manage(request.actor_role)
    channel = str(request.payload.get("channel", "arena_main"))
    return _push("twitch", {"channel": channel, "status": "connected"})


@app.post("/integrations/youtube/connect")
async def connect_youtube(request: IntegrationSyncRequest) -> dict[str, Any]:
    _assert_manage(request.actor_role)
    channel = str(request.payload.get("channel", "arena_live"))
    return _push("youtube", {"channel": channel, "status": "connected"})


@app.post("/integrations/game-api/sync")
async def sync_game_api(request: IntegrationSyncRequest) -> dict[str, Any]:
    _assert_manage(request.actor_role)
    provider = str(request.payload.get("provider", "steam"))
    return _push("game_api", {"provider": provider, "fetched_matches": int(request.payload.get("fetched_matches", 1))})


@app.get("/integrations/history")
async def get_history(system_name: str | None = None) -> dict[str, Any]:
    items = [item.model_dump(mode="json") for item in history if not system_name or item.system_name == system_name]
    return {"items": items, "count": len(items)}
