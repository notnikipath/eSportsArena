from shared.esports_common import (
    StreamProvider,
    availability_pct,
    calculate_mape,
    detect_cheat_risk,
    estimate_stream_delay_sec,
    is_cheat_suspected,
    predict_win_probability,
)


def test_stream_delay_estimate() -> None:
    value = estimate_stream_delay_sec(StreamProvider.HLS, viewers=42000, balanced=True)
    assert value > 0


def test_mape_and_win_probability() -> None:
    mape = calculate_mape([30, 40, 50], [33, 39, 52])
    assert mape >= 0

    win = predict_win_probability(team_a_rating=1650, team_b_rating=1580, recent_form_delta=0.3)
    assert 0 < win < 1


def test_cheat_helpers_and_availability() -> None:
    score = detect_cheat_risk([14, 16, 13, 42])
    assert score >= 0
    assert is_cheat_suspected([14, 16, 13, 42], threshold=1.5)
    assert availability_pct(43170, 43200) > 99

