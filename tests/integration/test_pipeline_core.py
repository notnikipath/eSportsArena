from pathlib import Path

from fastapi.testclient import TestClient

from tests.integration.helpers import load_module

ROOT = Path(__file__).resolve().parents[2]

tournament_module = load_module("tournament_module", ROOT / "tournament-service" / "app" / "main.py")
match_module = load_module("match_module", ROOT / "match-service" / "app" / "main.py")
interaction_module = load_module("interaction_module", ROOT / "interaction-service" / "app" / "main.py")
stats_module = load_module("stats_module", ROOT / "stats-service" / "app" / "main.py")
team_module = load_module("team_module", ROOT / "team-service" / "app" / "main.py")
streaming_module = load_module("streaming_module", ROOT / "streaming-service" / "app" / "main.py")
notification_module = load_module("notification_module", ROOT / "notification-service" / "app" / "main.py")

tournament_client = TestClient(tournament_module.app)
match_client = TestClient(match_module.app)
interaction_client = TestClient(interaction_module.app)
stats_client = TestClient(stats_module.app)
team_client = TestClient(team_module.app)
streaming_client = TestClient(streaming_module.app)
notification_client = TestClient(notification_module.app)


def test_auth_and_access_flow() -> None:
    challenge = team_client.post(
        "/auth/challenge/start",
        json={"user_id": "USR-ORG-1", "password": "org123"},
    )
    assert challenge.status_code == 200

    verify = team_client.post(
        "/auth/challenge/verify",
        json={"challenge_id": challenge.json()["challenge_id"], "otp_code": "123456"},
    )
    assert verify.status_code == 200
    assert "access_token" in verify.json()

    access = team_client.post(
        "/access/check",
        json={"user_id": "USR-ORG-1", "action": "match:manage", "resource_type": "match", "resource_id": "MCH-OPEN-001"},
    )
    assert access.status_code == 200
    assert access.json()["allowed"] is True


def test_match_stream_and_stats_flow() -> None:
    match = match_client.get("/matches/MCH-OPEN-001")
    assert match.status_code == 200

    stream = streaming_client.post(
        "/streams/create",
        json={
            "match_id": "MCH-OPEN-001",
            "provider": "hls",
            "language": "ru",
            "actor_id": "USR-ORG-1",
            "actor_role": "organizer",
        },
    )
    assert stream.status_code == 200

    update = match_client.post(
        "/matches/MCH-OPEN-001/status",
        json={
            "status": "live",
            "score": {"team_a": 0, "team_b": 0},
            "actor_id": "USR-ORG-1",
            "actor_role": "organizer",
        },
    )
    assert update.status_code == 200
    assert update.json()["status"] == "live"

    job = stats_client.post("/stats/collect/start", json={"match_id": "MCH-OPEN-001"})
    assert job.status_code == 200

    fan_notice = notification_client.post(
        "/notify/fans",
        json={
            "match_id": "MCH-OPEN-001",
            "teams": ["TEAM-ASTRA", "TEAM-NEON"],
            "stream_url": stream.json()["stream_url"],
            "actor_role": "organizer",
        },
    )
    assert fan_notice.status_code == 200


def test_interaction_and_prediction_flow() -> None:
    poll = interaction_client.post(
        "/interaction/polls",
        json={
            "match_id": "MCH-OPEN-001",
            "vote_type": "mvp",
            "question": "Who is MVP?",
            "options": ["AstraOne", "NeonFox", "NeonAce"],
            "actor_id": "USR-ORG-1",
            "actor_role": "organizer",
        },
    )
    assert poll.status_code == 200

    vote = interaction_client.post(
        "/interaction/votes",
        json={"poll_id": poll.json()["poll_id"], "user_id": "USR-FAN-1", "option": "AstraOne"},
    )
    assert vote.status_code == 200
    assert vote.json()["total_votes"] == 1

    outcome = stats_client.post(
        "/stats/predict/outcome",
        json={"team_a_rating": 1680, "team_b_rating": 1625, "recent_form_delta": 0.7},
    )
    assert outcome.status_code == 200
    assert outcome.json()["team_a_win_probability"] > 0.5

    cheat = stats_client.post(
        "/stats/cheat/detect",
        json={"match_id": "MCH-OPEN-001", "metric": "headshot_pct", "values": [24, 26, 25, 88], "threshold": 1.5},
    )
    assert cheat.status_code == 200
    assert cheat.json()["suspected"] is True

