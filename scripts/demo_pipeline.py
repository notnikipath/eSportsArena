from __future__ import annotations

import json
import urllib.request

BASE = "http://localhost:8680"


def request(method: str, path: str, payload: dict | None = None) -> dict:
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode("utf-8"))


if __name__ == "__main__":
    challenge = request("POST", "/auth/challenge/start", {"user_id": "USR-ORG-1", "password": "org123"})
    token = request("POST", "/auth/challenge/verify", {"challenge_id": challenge["challenge_id"], "otp_code": "123456"})

    workflow = request(
        "POST",
        "/workflow/start-match",
        {
            "match_id": "MCH-OPEN-001",
            "user_id": "USR-ORG-1",
            "arena_id": "ARENA-DEMO",
            "actor_role": "organizer",
            "provider": "hls",
        },
    )

    finish = request(
        "POST",
        "/workflow/finish-match",
        {
            "match_id": "MCH-OPEN-001",
            "user_id": "USR-ORG-1",
            "score_team_a": 2,
            "score_team_b": 1,
            "actor_role": "organizer",
        },
    )

    print(json.dumps({"token": token, "workflow": workflow, "finish": finish}, ensure_ascii=False, indent=2))
