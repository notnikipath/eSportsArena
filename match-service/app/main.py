from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException

from shared.esports_common import (
    MatchCreateRequest,
    MatchRecord,
    MatchStatus,
    MatchStatusUpdateRequest,
    Role,
    Settings,
    build_audit_event,
    has_permission,
)

settings = Settings(service_name="match-service", service_port=8602)
app = FastAPI(title="eSports Arena Match Service", version="1.0.0")

matches: dict[str, MatchRecord] = {}
audit_log: list[dict[str, Any]] = []


def _assert_permission(role: Role, action: str) -> None:
    if not has_permission(role, action):
        raise HTTPException(status_code=403, detail=f"Role {role.value} cannot perform {action}")


def _audit(actor_id: str, actor_role: Role, action: str, object_id: str, details: dict[str, Any] | None = None) -> None:
    audit_log.append(
        build_audit_event(
            actor_id=actor_id,
            actor_role=actor_role,
            action=action,
            object_type="match",
            object_id=object_id,
            details=details or {},
        ).model_dump(mode="json")
    )


def _seed() -> None:
    scheduled_at = datetime.now(UTC) + timedelta(minutes=45)
    seeded = MatchRecord(
        match_id="MCH-OPEN-001",
        tournament_id="TRN-CS-MAJOR-001",
        round_label="Upper Bracket R1",
        team_a_id="TEAM-ASTRA",
        team_b_id="TEAM-NEON",
        scheduled_at=scheduled_at,
        map_pool=["de_mirage", "de_nuke", "de_inferno"],
        server_region="ru-central",
    )
    matches[seeded.match_id] = seeded


_seed()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.get("/matches")
async def list_matches(
    tournament_id: str | None = None,
    status: MatchStatus | None = None,
    actor_role: Role = Role.SPECTATOR,
) -> dict[str, Any]:
    _assert_permission(actor_role, "match:read")
    items = []
    for item in matches.values():
        if tournament_id and item.tournament_id != tournament_id:
            continue
        if status and item.status != status:
            continue
        items.append(item.model_dump(mode="json"))
    return {"items": items, "count": len(items)}


@app.get("/matches/{match_id}")
async def get_match(match_id: str, actor_role: Role = Role.SPECTATOR) -> dict[str, Any]:
    _assert_permission(actor_role, "match:read")
    match = matches.get(match_id)
    if match is None:
        raise HTTPException(status_code=404, detail="Match not found")
    return match.model_dump(mode="json")


@app.post("/matches")
async def create_match(request: MatchCreateRequest) -> dict[str, Any]:
    _assert_permission(request.actor_role, "match:manage")
    match = MatchRecord(
        match_id=f"MCH-{uuid4().hex[:10].upper()}",
        tournament_id=request.tournament_id,
        round_label=request.round_label,
        team_a_id=request.team_a_id,
        team_b_id=request.team_b_id,
        scheduled_at=request.scheduled_at,
        map_pool=request.map_pool,
    )
    matches[match.match_id] = match
    _audit(request.actor_id, request.actor_role, "match.create", match.match_id)
    return match.model_dump(mode="json")


@app.post("/matches/{match_id}/status")
async def update_status(match_id: str, request: MatchStatusUpdateRequest) -> dict[str, Any]:
    _assert_permission(request.actor_role, "match:manage")
    match = matches.get(match_id)
    if match is None:
        raise HTTPException(status_code=404, detail="Match not found")

    match.status = request.status
    if request.score:
        match.score = {
            "team_a": int(request.score.get("team_a", match.score.get("team_a", 0))),
            "team_b": int(request.score.get("team_b", match.score.get("team_b", 0))),
        }

    _audit(
        request.actor_id,
        request.actor_role,
        "match.update_status",
        match_id,
        {"status": request.status.value, "score": match.score},
    )
    return match.model_dump(mode="json")


@app.post("/matches/{match_id}/result/ingest")
async def ingest_result(
    match_id: str, score_team_a: int, score_team_b: int, actor_role: Role = Role.ORGANIZER
) -> dict[str, Any]:
    _assert_permission(actor_role, "match:manage")
    match = matches.get(match_id)
    if match is None:
        raise HTTPException(status_code=404, detail="Match not found")

    match.score = {"team_a": score_team_a, "team_b": score_team_b}
    match.status = MatchStatus.FINISHED
    return match.model_dump(mode="json")


@app.get("/audit")
async def get_audit(limit: int = 200, actor_role: Role = Role.ADMIN) -> dict[str, Any]:
    _assert_permission(actor_role, "audit:read")
    return {"items": audit_log[-limit:], "count": len(audit_log)}
