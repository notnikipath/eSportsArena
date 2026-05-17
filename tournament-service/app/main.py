from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from shared.esports_common import (
    Discipline,
    Role,
    Settings,
    Tournament,
    TournamentCreateRequest,
    TournamentStage,
    build_audit_event,
    has_permission,
)

settings = Settings(service_name="tournament-service", service_port=8601)
app = FastAPI(title="eSports Arena Tournament Service", version="1.0.0")

tournaments: dict[str, Tournament] = {}
audit_log: list[dict[str, Any]] = []


class RegisterTeamRequest(BaseModel):
    team_id: str
    actor_id: str
    actor_role: Role


RegisterTeamRequest.model_rebuild()


def _assert_permission(role: Role, action: str) -> None:
    if not has_permission(role, action):
        raise HTTPException(status_code=403, detail=f"Role {role.value} cannot perform {action}")


def _audit(actor_id: str, actor_role: Role, action: str, object_id: str, details: dict[str, Any] | None = None) -> None:
    audit_log.append(
        build_audit_event(
            actor_id=actor_id,
            actor_role=actor_role,
            action=action,
            object_type="tournament",
            object_id=object_id,
            details=details or {},
        ).model_dump(mode="json")
    )


def _seed() -> None:
    seeded = Tournament(
        tournament_id="TRN-CS-MAJOR-001",
        arena_id="ARENA-DEMO",
        title="Arena Spring Clash 2026",
        discipline=Discipline.SHOOTER,
        stage=TournamentStage.DOUBLE_ELIM,
        start_at="2026-06-20T12:00:00Z",
        teams_registered=["TEAM-ASTRA", "TEAM-NEON"],
        status="group_stage",
    )
    tournaments[seeded.tournament_id] = seeded


_seed()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.get("/disciplines")
async def disciplines() -> dict[str, Any]:
    return {"items": [item.value for item in Discipline], "count": len(Discipline)}


@app.get("/tournaments")
async def list_tournaments(arena_id: str = "ARENA-DEMO", actor_role: Role = Role.SPECTATOR) -> dict[str, Any]:
    _assert_permission(actor_role, "tournament:read")
    items = [item.model_dump(mode="json") for item in tournaments.values() if item.arena_id == arena_id]
    return {"items": items, "count": len(items)}


@app.get("/tournaments/{tournament_id}")
async def get_tournament(tournament_id: str, actor_role: Role = Role.SPECTATOR) -> dict[str, Any]:
    _assert_permission(actor_role, "tournament:read")
    tournament = tournaments.get(tournament_id)
    if tournament is None:
        raise HTTPException(status_code=404, detail="Tournament not found")
    return tournament.model_dump(mode="json")


@app.post("/tournaments")
async def create_tournament(request: TournamentCreateRequest) -> dict[str, Any]:
    _assert_permission(request.actor_role, "tournament:create")
    tournament = Tournament(
        tournament_id=f"TRN-{uuid4().hex[:10].upper()}",
        arena_id=request.arena_id,
        title=request.title,
        discipline=request.discipline,
        stage=request.stage,
        start_at=request.start_at,
    )
    tournaments[tournament.tournament_id] = tournament
    _audit(request.actor_id, request.actor_role, "tournament.create", tournament.tournament_id)
    return tournament.model_dump(mode="json")


@app.post("/tournaments/{tournament_id}/register-team")
async def register_team(tournament_id: str, request: RegisterTeamRequest) -> dict[str, Any]:
    _assert_permission(request.actor_role, "tournament:manage")
    tournament = tournaments.get(tournament_id)
    if tournament is None:
        raise HTTPException(status_code=404, detail="Tournament not found")

    if request.team_id not in tournament.teams_registered:
        tournament.teams_registered.append(request.team_id)

    _audit(
        request.actor_id,
        request.actor_role,
        "tournament.register_team",
        tournament_id,
        {"team_id": request.team_id},
    )
    return {
        "tournament_id": tournament_id,
        "teams_registered": tournament.teams_registered,
        "count": len(tournament.teams_registered),
    }


@app.get("/audit")
async def get_audit(limit: int = 200, actor_role: Role = Role.ADMIN) -> dict[str, Any]:
    _assert_permission(actor_role, "audit:read")
    return {"items": audit_log[-limit:], "count": len(audit_log)}
