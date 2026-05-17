from shared.esports_common import parse_interaction_text, recommend_highlight_rounds, recommend_mvp_candidates


def test_parse_interaction_text() -> None:
    parsed = parse_interaction_text("MVP vote now")
    assert parsed["intent"] == "vote"


def test_recommend_highlight_rounds() -> None:
    highlights = recommend_highlight_rounds(
        [
            {"round": "R1", "metric": "kills", "value": 8},
            {"round": "R1", "metric": "kills", "value": 6},
            {"round": "R2", "metric": "kills", "value": 12},
        ]
    )
    assert highlights


def test_recommend_mvp_candidates() -> None:
    players = [
        {"nickname": "AstraOne", "impact": 88, "kda": 1.4},
        {"nickname": "NeonFox", "impact": 75, "kda": 1.1},
        {"nickname": "EchoRay", "impact": 67, "kda": 1.2},
    ]
    result = recommend_mvp_candidates(players)
    assert result[0] == "AstraOne"
