from __future__ import annotations

from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

from shared.esports_common import (
    MatchStatus,
    ProcessMatchWorkflowResult,
    Role,
    Settings,
    StreamProvider,
    TwoFactorStartRequest,
    TwoFactorVerifyRequest,
    verify_token,
)


class GatewaySettings(BaseSettings):
    service_name: str = "api-gateway"
    service_port: int = 8600

    tournament_service_url: str = "http://tournament-service:8601"
    match_service_url: str = "http://match-service:8602"
    interaction_service_url: str = "http://interaction-service:8603"
    stats_service_url: str = "http://stats-service:8604"
    team_service_url: str = "http://team-service:8605"
    notification_service_url: str = "http://notification-service:8606"
    streaming_service_url: str = "http://streaming-service:8607"

    jwt_secret: str = Settings().jwt_secret

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = GatewaySettings()
app = FastAPI(title="eSports Arena API Gateway", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5182",
        "http://127.0.0.1:5182",
        "http://localhost:5178",
        "http://127.0.0.1:5178",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class VerifyAuthRequest(BaseModel):
    token: str


class StartMatchRequest(BaseModel):
    match_id: str
    user_id: str
    arena_id: str = "ARENA-DEMO"
    actor_role: Role = Role.ORGANIZER
    provider: StreamProvider = StreamProvider.HLS


class FinishMatchRequest(BaseModel):
    match_id: str
    user_id: str
    score_team_a: int
    score_team_b: int
    actor_role: Role = Role.ORGANIZER


VerifyAuthRequest.model_rebuild()
StartMatchRequest.model_rebuild()
FinishMatchRequest.model_rebuild()


async def _post_json(client: httpx.AsyncClient, url: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = await client.post(url, json=payload)
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


async def _get_json(client: httpx.AsyncClient, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    response = await client.get(url, params=params)
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


def _service_urls() -> dict[str, str]:
    return {
        "tournament": settings.tournament_service_url,
        "match": settings.match_service_url,
        "interaction": settings.interaction_service_url,
        "stats": settings.stats_service_url,
        "team": settings.team_service_url,
        "notification": settings.notification_service_url,
        "streaming": settings.streaming_service_url,
    }


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.get("/services/health")
async def service_health() -> dict[str, Any]:
    statuses: dict[str, Any] = {}
    async with httpx.AsyncClient(timeout=8.0) as client:
        for name, base_url in _service_urls().items():
            try:
                statuses[name] = await _get_json(client, f"{base_url}/health")
            except HTTPException as exc:
                statuses[name] = {"status": "error", "detail": exc.detail}
            except httpx.HTTPError as exc:
                statuses[name] = {"status": "error", "detail": str(exc)}
    return statuses


@app.post("/auth/challenge/start")
async def auth_start(request: TwoFactorStartRequest) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        return await _post_json(
            client,
            f"{settings.team_service_url}/auth/challenge/start",
            request.model_dump(mode="json"),
        )


@app.post("/auth/challenge/verify")
async def auth_verify(request: TwoFactorVerifyRequest) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        return await _post_json(
            client,
            f"{settings.team_service_url}/auth/challenge/verify",
            request.model_dump(mode="json"),
        )


@app.post("/auth/verify")
async def verify_auth(request: VerifyAuthRequest) -> dict[str, Any]:
    payload = verify_token(request.token, settings.jwt_secret)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload


@app.post("/workflow/start-match")
async def start_match(request: StartMatchRequest) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=25.0) as client:
        access = await _post_json(
            client,
            f"{settings.team_service_url}/access/check",
            {
                "user_id": request.user_id,
                "action": "match:manage",
                "resource_type": "match",
                "resource_id": request.match_id,
            },
        )
        if not access["allowed"]:
            raise HTTPException(status_code=403, detail=access["reason"])

        match = await _get_json(client, f"{settings.match_service_url}/matches/{request.match_id}")

        stream = await _post_json(
            client,
            f"{settings.streaming_service_url}/streams/create",
            {
                "match_id": request.match_id,
                "provider": request.provider.value,
                "language": "ru",
                "actor_id": request.user_id,
                "actor_role": request.actor_role.value,
            },
        )

        notification = await _post_json(
            client,
            f"{settings.notification_service_url}/notify/fans",
            {
                "match_id": request.match_id,
                "teams": [match["team_a_id"], match["team_b_id"]],
                "stream_url": stream["stream_url"],
                "actor_role": request.actor_role.value,
            },
        )

        status_update = await _post_json(
            client,
            f"{settings.match_service_url}/matches/{request.match_id}/status",
            {
                "status": MatchStatus.LIVE.value,
                "score": match.get("score", {"team_a": 0, "team_b": 0}),
                "actor_id": request.user_id,
                "actor_role": request.actor_role.value,
            },
        )

        stats_job = await _post_json(
            client,
            f"{settings.stats_service_url}/stats/collect/start",
            {"match_id": request.match_id},
        )

    result = ProcessMatchWorkflowResult(
        match=match,
        stream=stream,
        notification=notification,
        status_update=status_update,
        stats_job=stats_job,
    )
    return result.model_dump(mode="json")


@app.post("/workflow/finish-match")
async def finish_match(request: FinishMatchRequest) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=20.0) as client:
        access = await _post_json(
            client,
            f"{settings.team_service_url}/access/check",
            {
                "user_id": request.user_id,
                "action": "match:manage",
                "resource_type": "match",
                "resource_id": request.match_id,
            },
        )
        if not access["allowed"]:
            raise HTTPException(status_code=403, detail=access["reason"])

        status_update = await _post_json(
            client,
            f"{settings.match_service_url}/matches/{request.match_id}/status",
            {
                "status": MatchStatus.FINISHED.value,
                "score": {"team_a": request.score_team_a, "team_b": request.score_team_b},
                "actor_id": request.user_id,
                "actor_role": request.actor_role.value,
            },
        )

        await _post_json(
            client,
            f"{settings.notification_service_url}/notify/send",
            {
                "channel": "in_app",
                "recipient": "fans",
                "subject": f"Match {request.match_id} finished",
                "body": f"Final score: {request.score_team_a}:{request.score_team_b}",
                "severity": "info",
                "actor_role": request.actor_role.value,
            },
        )

        stats = await _get_json(client, f"{settings.stats_service_url}/stats/match/{request.match_id}")

    return {
        "match_id": request.match_id,
        "status": status_update.get("status"),
        "score": status_update.get("score"),
        "stats_events": stats.get("count", 0),
    }


@app.get("/dashboard/{arena_id}/{user_id}")
async def dashboard(arena_id: str, user_id: str, actor_role: Role = Role.ORGANIZER) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=20.0) as client:
        tournaments = await _get_json(
            client,
            f"{settings.tournament_service_url}/tournaments",
            {"arena_id": arena_id, "actor_role": actor_role.value},
        )
        matches = await _get_json(client, f"{settings.match_service_url}/matches", {"actor_role": actor_role.value})
        teams = await _get_json(
            client,
            f"{settings.team_service_url}/teams",
            {"arena_id": arena_id, "actor_role": actor_role.value},
        )
        users = await _get_json(client, f"{settings.team_service_url}/users", {"arena_id": arena_id})
        streams = await _get_json(client, f"{settings.streaming_service_url}/streams")
        integrations = await _get_json(client, f"{settings.streaming_service_url}/integrations/history")
        polls = await _get_json(client, f"{settings.interaction_service_url}/interaction/polls")
        kpi = await _get_json(client, f"{settings.stats_service_url}/stats/kpi", {"arena_id": arena_id})
        anomalies = await _get_json(client, f"{settings.stats_service_url}/stats/anomalies")
        notifications = await _get_json(client, f"{settings.notification_service_url}/notify/history")

    return {
        "arena_id": arena_id,
        "user_id": user_id,
        "tournaments": tournaments,
        "matches": matches,
        "teams": teams,
        "users": users,
        "streams": streams,
        "integrations": integrations,
        "polls": polls,
        "kpi": kpi,
        "anomalies": anomalies,
        "notifications": notifications,
    }
