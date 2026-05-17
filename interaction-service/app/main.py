from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from shared.esports_common import (
    Poll,
    PollCreateRequest,
    PollResult,
    Role,
    Settings,
    VoteSubmitRequest,
    has_permission,
    parse_interaction_text,
    recommend_mvp_candidates,
)

settings = Settings(service_name="interaction-service", service_port=8603)
app = FastAPI(title="eSports Arena Interaction Service", version="1.0.0")

polls: dict[str, Poll] = {}
votes: dict[str, dict[str, int]] = {}
user_votes: set[tuple[str, str]] = set()


class ParseRequest(BaseModel):
    text: str


class MvpSuggestRequest(BaseModel):
    players: list[dict[str, Any]]


ParseRequest.model_rebuild()
MvpSuggestRequest.model_rebuild()


def _assert_create(role: Role) -> None:
    if not has_permission(role, "interaction:create"):
        raise HTTPException(status_code=403, detail="Forbidden")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.post("/interaction/parse")
async def parse(request: ParseRequest) -> dict[str, Any]:
    return parse_interaction_text(request.text)


@app.post("/interaction/polls")
async def create_poll(request: PollCreateRequest) -> dict[str, Any]:
    _assert_create(request.actor_role)
    poll = Poll(
        poll_id=f"PLL-{uuid4().hex[:10].upper()}",
        match_id=request.match_id,
        vote_type=request.vote_type,
        question=request.question,
        options=request.options,
    )
    polls[poll.poll_id] = poll
    votes[poll.poll_id] = {option: 0 for option in request.options}
    return poll.model_dump(mode="json")


@app.get("/interaction/polls")
async def list_polls(match_id: str | None = None) -> dict[str, Any]:
    items = [item.model_dump(mode="json") for item in polls.values() if not match_id or item.match_id == match_id]
    return {"items": items, "count": len(items)}


@app.get("/interaction/polls/{poll_id}")
async def get_poll(poll_id: str) -> dict[str, Any]:
    poll = polls.get(poll_id)
    if poll is None:
        raise HTTPException(status_code=404, detail="Poll not found")
    return poll.model_dump(mode="json")


@app.post("/interaction/votes")
async def submit_vote(request: VoteSubmitRequest) -> dict[str, Any]:
    poll = polls.get(request.poll_id)
    if poll is None:
        raise HTTPException(status_code=404, detail="Poll not found")
    if poll.status != "open":
        raise HTTPException(status_code=400, detail="Poll is closed")
    if request.option not in votes.get(request.poll_id, {}):
        raise HTTPException(status_code=400, detail="Invalid option")

    marker = (request.poll_id, request.user_id)
    if marker in user_votes:
        raise HTTPException(status_code=409, detail="User already voted")

    votes[request.poll_id][request.option] += 1
    user_votes.add(marker)
    result = PollResult(
        poll_id=request.poll_id,
        total_votes=sum(votes[request.poll_id].values()),
        breakdown=votes[request.poll_id],
    )
    return result.model_dump(mode="json")


@app.get("/interaction/polls/{poll_id}/results")
async def get_results(poll_id: str) -> dict[str, Any]:
    if poll_id not in polls:
        raise HTTPException(status_code=404, detail="Poll not found")
    result = PollResult(
        poll_id=poll_id,
        total_votes=sum(votes.get(poll_id, {}).values()),
        breakdown=votes.get(poll_id, {}),
    )
    return result.model_dump(mode="json")


@app.post("/interaction/mvp/recommend")
async def mvp_recommend(request: MvpSuggestRequest) -> dict[str, Any]:
    return {"items": recommend_mvp_candidates(request.players)}
