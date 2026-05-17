from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Discipline(str, Enum):
    MOBA = "moba"
    SHOOTER = "shooter"
    STRATEGY = "strategy"
    FIGHTING = "fighting"
    SPORTS_SIM = "sports_sim"


class TournamentStage(str, Enum):
    SINGLE_ELIM = "single_elimination"
    DOUBLE_ELIM = "double_elimination"
    GROUP_STAGE = "group_stage"
    SWISS = "swiss"


class MatchStatus(str, Enum):
    SCHEDULED = "scheduled"
    LIVE = "live"
    FINISHED = "finished"
    POSTPONED = "postponed"
    CANCELED = "canceled"


class StreamProvider(str, Enum):
    HLS = "hls"
    WEBRTC = "webrtc"
    TWITCH = "twitch"
    YOUTUBE = "youtube"


class VoteType(str, Enum):
    MVP = "mvp"
    PREDICTION = "prediction"


class InteractionIntent(str, Enum):
    VOTE = "vote"
    MATCH_STATUS = "match_status"
    STREAM_LINK = "stream_link"
    UNKNOWN = "unknown"


class NotificationChannel(str, Enum):
    PUSH = "push"
    EMAIL = "email"
    SMS = "sms"
    TELEGRAM = "telegram"
    WEBHOOK = "webhook"
    IN_APP = "in_app"


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class Role(str, Enum):
    ADMIN = "admin"
    ORGANIZER = "organizer"
    CAPTAIN = "captain"
    PLAYER = "player"
    SPECTATOR = "spectator"


class TournamentCreateRequest(BaseModel):
    arena_id: str
    title: str
    discipline: Discipline
    stage: TournamentStage
    start_at: datetime
    actor_id: str
    actor_role: Role


class Tournament(BaseModel):
    tournament_id: str
    arena_id: str
    title: str
    discipline: Discipline
    stage: TournamentStage
    start_at: datetime
    status: str = "registration"
    teams_registered: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PlayerProfile(BaseModel):
    player_id: str
    nickname: str
    game_role: str
    kda: float = Field(default=0, ge=0)
    country: str = "KZ"


class TeamCreateRequest(BaseModel):
    arena_id: str
    name: str
    tag: str
    discipline: Discipline
    captain_user_id: str
    actor_id: str
    actor_role: Role


class TeamProfile(BaseModel):
    team_id: str
    arena_id: str
    name: str
    tag: str
    discipline: Discipline
    rating: int = 1000
    captain_user_id: str
    players: list[PlayerProfile] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class TransferRequest(BaseModel):
    player: PlayerProfile
    from_team_id: str | None = None
    actor_id: str
    actor_role: Role


class MatchCreateRequest(BaseModel):
    tournament_id: str
    round_label: str
    team_a_id: str
    team_b_id: str
    scheduled_at: datetime
    map_pool: list[str] = Field(default_factory=list)
    actor_id: str
    actor_role: Role


class MatchRecord(BaseModel):
    match_id: str
    tournament_id: str
    round_label: str
    team_a_id: str
    team_b_id: str
    scheduled_at: datetime
    status: MatchStatus = MatchStatus.SCHEDULED
    map_pool: list[str] = Field(default_factory=list)
    server_region: str = "eu-central"
    score: dict[str, int] = Field(default_factory=lambda: {"team_a": 0, "team_b": 0})
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class MatchStatusUpdateRequest(BaseModel):
    status: MatchStatus
    score: dict[str, int] = Field(default_factory=dict)
    actor_id: str
    actor_role: Role


class StreamCreateRequest(BaseModel):
    match_id: str
    provider: StreamProvider = StreamProvider.HLS
    language: str = Field(default="ru", pattern="^(ru|en)$")
    actor_id: str
    actor_role: Role


class StreamSession(BaseModel):
    stream_id: str
    match_id: str
    provider: StreamProvider
    stream_url: str
    ingest_url: str
    status: str = "live"
    delay_sec: float = Field(ge=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class MatchStatsEvent(BaseModel):
    event_id: str
    match_id: str
    metric: str
    value: float
    source: str = "collector"
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PollCreateRequest(BaseModel):
    match_id: str
    vote_type: VoteType
    question: str
    options: list[str] = Field(min_length=2)
    actor_id: str
    actor_role: Role


class Poll(BaseModel):
    poll_id: str
    match_id: str
    vote_type: VoteType
    question: str
    options: list[str]
    status: str = "open"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class VoteSubmitRequest(BaseModel):
    poll_id: str
    user_id: str
    option: str


class PollResult(BaseModel):
    poll_id: str
    total_votes: int
    breakdown: dict[str, int] = Field(default_factory=dict)


class UserAccount(BaseModel):
    user_id: str
    arena_id: str
    role: Role
    email: str
    phone: str
    enabled: bool = True
    two_factor_enabled: bool = True


class TwoFactorStartRequest(BaseModel):
    user_id: str
    password: str


class TwoFactorChallenge(BaseModel):
    challenge_id: str
    user_id: str
    otp_code: str
    channel: NotificationChannel = NotificationChannel.SMS
    expires_at: datetime


class TwoFactorVerifyRequest(BaseModel):
    challenge_id: str
    otp_code: str


class AccessCheckRequest(BaseModel):
    user_id: str
    action: str
    resource_type: str = "match"
    resource_id: str = "*"


class AccessCheckResult(BaseModel):
    allowed: bool
    reason: str
    checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class IntegrationSyncRequest(BaseModel):
    system_name: str
    payload: dict[str, Any] = Field(default_factory=dict)
    actor_id: str
    actor_role: Role


class IntegrationSyncResult(BaseModel):
    sync_id: str
    system_name: str
    status: str
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class NotificationRequest(BaseModel):
    channel: NotificationChannel
    recipient: str
    subject: str
    body: str
    severity: Severity = Severity.INFO
    actor_role: Role


class AuditEvent(BaseModel):
    event_id: str
    actor_id: str
    actor_role: Role | str
    action: str
    object_type: str
    object_id: str
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ProcessMatchWorkflowResult(BaseModel):
    match: dict[str, Any]
    stream: dict[str, Any]
    notification: dict[str, Any]
    status_update: dict[str, Any]
    stats_job: dict[str, Any]
    completed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
