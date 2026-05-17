from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException

from shared.esports_common import (
    AccessCheckRequest,
    AccessCheckResult,
    NotificationChannel,
    PlayerProfile,
    Role,
    Settings,
    TeamCreateRequest,
    TeamProfile,
    TransferRequest,
    TwoFactorChallenge,
    TwoFactorStartRequest,
    TwoFactorVerifyRequest,
    UserAccount,
    build_audit_event,
    has_permission,
    sign_token,
)

settings = Settings(service_name="team-service", service_port=8605)
app = FastAPI(title="eSports Arena Team Service", version="1.0.0")

users: dict[str, UserAccount] = {
    "USR-ADMIN-1": UserAccount(
        user_id="USR-ADMIN-1",
        arena_id="ARENA-DEMO",
        role=Role.ADMIN,
        email="admin@arena.local",
        phone="+77000000001",
    ),
    "USR-ORG-1": UserAccount(
        user_id="USR-ORG-1",
        arena_id="ARENA-DEMO",
        role=Role.ORGANIZER,
        email="organizer@arena.local",
        phone="+77000000002",
    ),
    "USR-CAP-1": UserAccount(
        user_id="USR-CAP-1",
        arena_id="ARENA-DEMO",
        role=Role.CAPTAIN,
        email="captain@arena.local",
        phone="+77000000003",
    ),
    "USR-FAN-1": UserAccount(
        user_id="USR-FAN-1",
        arena_id="ARENA-DEMO",
        role=Role.SPECTATOR,
        email="fan@arena.local",
        phone="+77000000004",
    ),
}

passwords = {
    "USR-ADMIN-1": "admin123",
    "USR-ORG-1": "org123",
    "USR-CAP-1": "cap123",
    "USR-FAN-1": "fan123",
}

teams: dict[str, TeamProfile] = {
    "TEAM-ASTRA": TeamProfile(
        team_id="TEAM-ASTRA",
        arena_id="ARENA-DEMO",
        name="Astra Wolves",
        tag="AST",
        discipline="shooter",
        rating=1680,
        captain_user_id="USR-CAP-1",
        players=[
            PlayerProfile(player_id="PLR-A1", nickname="AstraOne", game_role="entry", kda=1.28, country="KZ"),
            PlayerProfile(player_id="PLR-A2", nickname="AstraTwo", game_role="support", kda=1.11, country="RU"),
        ],
    ),
    "TEAM-NEON": TeamProfile(
        team_id="TEAM-NEON",
        arena_id="ARENA-DEMO",
        name="Neon Falcons",
        tag="NEO",
        discipline="shooter",
        rating=1625,
        captain_user_id="USR-ORG-1",
        players=[
            PlayerProfile(player_id="PLR-N1", nickname="NeonFox", game_role="sniper", kda=1.22, country="KZ"),
            PlayerProfile(player_id="PLR-N2", nickname="NeonAce", game_role="lurker", kda=1.07, country="UA"),
        ],
    ),
}

challenges: dict[str, TwoFactorChallenge] = {}
audit_log: list[dict[str, Any]] = []


def _audit(actor_id: str, actor_role: Role | str, action: str, object_id: str, details: dict[str, Any] | None = None) -> None:
    audit_log.append(
        build_audit_event(
            actor_id=actor_id,
            actor_role=actor_role,
            action=action,
            object_type="team",
            object_id=object_id,
            details=details or {},
        ).model_dump(mode="json")
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.post("/auth/challenge/start")
async def start_challenge(request: TwoFactorStartRequest) -> dict[str, Any]:
    user = users.get(request.user_id)
    if user is None or not user.enabled:
        raise HTTPException(status_code=404, detail="User not found or disabled")
    if passwords.get(request.user_id) != request.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    challenge = TwoFactorChallenge(
        challenge_id=str(uuid4()),
        user_id=request.user_id,
        otp_code="123456",
        channel=NotificationChannel.SMS,
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
    )
    challenges[challenge.challenge_id] = challenge
    _audit(request.user_id, user.role, "auth.challenge.start", challenge.challenge_id)
    return {
        "challenge_id": challenge.challenge_id,
        "channel": challenge.channel.value,
        "delivery_hint": "***0001",
        "otp_preview": challenge.otp_code,
        "expires_at": challenge.expires_at,
    }


@app.post("/auth/challenge/verify")
async def verify_challenge(request: TwoFactorVerifyRequest) -> dict[str, Any]:
    challenge = challenges.get(request.challenge_id)
    if challenge is None:
        raise HTTPException(status_code=404, detail="Challenge not found")
    if challenge.expires_at < datetime.now(UTC):
        raise HTTPException(status_code=401, detail="Challenge expired")
    if challenge.otp_code != request.otp_code:
        raise HTTPException(status_code=401, detail="Invalid OTP")

    user = users[challenge.user_id]
    token = sign_token(
        {"sub": user.user_id, "arena_id": user.arena_id, "role": user.role.value},
        settings.jwt_secret,
        exp_minutes=240,
    )
    _audit(user.user_id, user.role, "auth.challenge.verify", challenge.challenge_id)
    return {"access_token": token, "token_type": "Bearer", "role": user.role.value, "arena_id": user.arena_id}


@app.post("/access/check")
async def access_check(request: AccessCheckRequest) -> dict[str, Any]:
    user = users.get(request.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    allowed = has_permission(user.role, request.action)
    reason = "permission_granted" if allowed else "permission_denied"
    _audit(user.user_id, user.role, "access.check", request.resource_id, {"action": request.action, "allowed": allowed})
    return AccessCheckResult(allowed=allowed, reason=reason).model_dump(mode="json")


@app.get("/users")
async def list_users(arena_id: str = "ARENA-DEMO") -> dict[str, Any]:
    items = [item.model_dump(mode="json") for item in users.values() if item.arena_id == arena_id]
    return {"items": items, "count": len(items)}


@app.get("/teams")
async def list_teams(arena_id: str = "ARENA-DEMO", actor_role: Role = Role.SPECTATOR) -> dict[str, Any]:
    if not has_permission(actor_role, "team:read"):
        raise HTTPException(status_code=403, detail="Forbidden")
    items = [item.model_dump(mode="json") for item in teams.values() if item.arena_id == arena_id]
    return {"items": items, "count": len(items)}


@app.get("/teams/{team_id}")
async def get_team(team_id: str, actor_role: Role = Role.SPECTATOR) -> dict[str, Any]:
    if not has_permission(actor_role, "team:read"):
        raise HTTPException(status_code=403, detail="Forbidden")
    team = teams.get(team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    return team.model_dump(mode="json")


@app.post("/teams")
async def create_team(request: TeamCreateRequest) -> dict[str, Any]:
    if not has_permission(request.actor_role, "team:manage"):
        raise HTTPException(status_code=403, detail="Forbidden")

    team = TeamProfile(
        team_id=f"TEAM-{uuid4().hex[:8].upper()}",
        arena_id=request.arena_id,
        name=request.name,
        tag=request.tag.upper(),
        discipline=request.discipline,
        captain_user_id=request.captain_user_id,
        players=[],
        rating=1200,
    )
    teams[team.team_id] = team
    _audit(request.actor_id, request.actor_role, "team.create", team.team_id)
    return team.model_dump(mode="json")


@app.post("/teams/{team_id}/transfers")
async def transfer_player(team_id: str, request: TransferRequest) -> dict[str, Any]:
    if not has_permission(request.actor_role, "team:manage"):
        raise HTTPException(status_code=403, detail="Forbidden")
    target = teams.get(team_id)
    if target is None:
        raise HTTPException(status_code=404, detail="Team not found")

    if request.from_team_id:
        source = teams.get(request.from_team_id)
        if source:
            source.players = [item for item in source.players if item.player_id != request.player.player_id]

    target.players = [item for item in target.players if item.player_id != request.player.player_id]
    target.players.append(request.player)

    _audit(
        request.actor_id,
        request.actor_role,
        "team.transfer",
        team_id,
        {"player_id": request.player.player_id, "from_team_id": request.from_team_id},
    )
    return target.model_dump(mode="json")


@app.get("/audit")
async def get_audit(limit: int = 200, actor_role: Role = Role.ADMIN) -> dict[str, Any]:
    if not has_permission(actor_role, "audit:read"):
        raise HTTPException(status_code=403, detail="Forbidden")
    return {"items": audit_log[-limit:], "count": len(audit_log)}
