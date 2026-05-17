from __future__ import annotations

from statistics import mean, pstdev

from .schemas import StreamProvider


def estimate_stream_delay_sec(provider: StreamProvider, viewers: int, balanced: bool = True) -> float:
    base = {
        StreamProvider.HLS: 8.0,
        StreamProvider.WEBRTC: 0.25,
        StreamProvider.TWITCH: 9.5,
        StreamProvider.YOUTUBE: 9.0,
    }[provider]
    viewer_penalty = min(max(viewers, 0) / 50000, 6.0)
    balancing_bonus = 1.6 if balanced else 0.0
    return round(max(0.12, base + viewer_penalty - balancing_bonus), 3)


def calculate_mape(actual: list[float], predicted: list[float]) -> float:
    if not actual or not predicted or len(actual) != len(predicted):
        return 0.0
    errors = []
    for a, p in zip(actual, predicted, strict=True):
        if a == 0:
            continue
        errors.append(abs((a - p) / a) * 100)
    if not errors:
        return 0.0
    return round(mean(errors), 3)


def predict_win_probability(team_a_rating: int, team_b_rating: int, recent_form_delta: float = 0) -> float:
    rating_gap = team_a_rating - team_b_rating
    elo_probability = 1 / (1 + 10 ** (-(rating_gap + recent_form_delta * 40) / 400))
    return round(min(max(elo_probability, 0.01), 0.99), 4)


def detect_cheat_risk(values: list[float]) -> float:
    if len(values) < 4:
        return 0.0
    sigma = pstdev(values)
    if sigma == 0:
        return 0.0
    z = abs(values[-1] - mean(values)) / sigma
    return round(z, 3)


def is_cheat_suspected(values: list[float], threshold: float = 3.2) -> bool:
    return detect_cheat_risk(values) >= threshold


def stats_refresh_ms(events_count: int, workers: int = 8) -> float:
    if events_count <= 0:
        return 100.0
    baseline = 1800 / max(workers, 1)
    return round(max(120.0, baseline + events_count * 0.12), 2)


def availability_pct(uptime_minutes: int, total_minutes: int) -> float:
    if total_minutes <= 0:
        return 0.0
    return round(min(max((uptime_minutes / total_minutes) * 100, 0.0), 100.0), 3)
