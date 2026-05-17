from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from shared.esports_common import NotificationChannel, NotificationRequest, Role, Settings, Severity, has_permission

settings = Settings(service_name="notification-service", service_port=8606)
app = FastAPI(title="eSports Arena Notification Service", version="1.0.0")

messages: list[dict[str, Any]] = []


class FanNotifyRequest(BaseModel):
    match_id: str
    teams: list[str]
    stream_url: str
    actor_role: Role


FanNotifyRequest.model_rebuild()


def _assert_send(role: Role) -> None:
    if not has_permission(role, "notification:send"):
        raise HTTPException(status_code=403, detail="Forbidden")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.post("/notify/send")
async def send(request: NotificationRequest) -> dict[str, Any]:
    _assert_send(request.actor_role)
    payload = request.model_dump(mode="json")
    payload["status"] = "queued"
    messages.append(payload)
    return payload


@app.post("/notify/fans")
async def notify_fans(request: FanNotifyRequest) -> dict[str, Any]:
    _assert_send(request.actor_role)
    payload = {
        "channel": NotificationChannel.IN_APP.value,
        "recipient": "fans",
        "subject": f"Match {request.match_id} is live",
        "body": f"Teams: {' vs '.join(request.teams)}. Watch now: {request.stream_url}",
        "severity": Severity.INFO.value,
        "status": "queued",
    }
    messages.append(payload)
    return payload


@app.get("/notify/history")
async def history(limit: int = 100) -> dict[str, Any]:
    return {"items": messages[-limit:], "count": len(messages)}
