from __future__ import annotations

from collections import Counter

from .schemas import InteractionIntent


def parse_interaction_text(text: str) -> dict[str, object]:
    normalized = text.lower().strip()
    if not normalized:
        return {"intent": InteractionIntent.UNKNOWN.value, "payload": {}, "confidence": 0.0}

    if "mvp" in normalized or "лучший" in normalized:
        return {"intent": InteractionIntent.VOTE.value, "payload": {"vote_type": "mvp"}, "confidence": 0.96}

    if "predict" in normalized or "прогноз" in normalized:
        return {"intent": InteractionIntent.VOTE.value, "payload": {"vote_type": "prediction"}, "confidence": 0.93}

    if "stream" in normalized or "трансля" in normalized:
        return {"intent": InteractionIntent.STREAM_LINK.value, "payload": {}, "confidence": 0.88}

    if "status" in normalized or "счёт" in normalized:
        return {"intent": InteractionIntent.MATCH_STATUS.value, "payload": {}, "confidence": 0.84}

    return {"intent": InteractionIntent.UNKNOWN.value, "payload": {}, "confidence": 0.42}


def recommend_highlight_rounds(events: list[dict[str, object]]) -> list[str]:
    kills_by_round: Counter[str] = Counter()
    for event in events:
        metric = str(event.get("metric", ""))
        if "kills" not in metric:
            continue
        round_label = str(event.get("round", "round-unknown"))
        kills_by_round[round_label] += int(float(event.get("value", 0)))
    return [label for label, _ in kills_by_round.most_common(3)]


def recommend_mvp_candidates(player_scores: list[dict[str, object]]) -> list[str]:
    if not player_scores:
        return []
    ordered = sorted(
        player_scores,
        key=lambda item: float(item.get("impact", 0)) * 0.6 + float(item.get("kda", 0)) * 0.4,
        reverse=True,
    )
    return [str(item.get("nickname", "unknown")) for item in ordered[:3]]
