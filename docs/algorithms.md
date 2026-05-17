# Algorithms and Rules

## 1. Stream balancing

When a match is started, `streaming-service` selects a node with minimal `active_viewers/capacity` ratio. This reduces expected stream delay under peak load.

## 2. ETA quality (MAPE)

`stats-service` computes MAPE:

`MAPE = mean(abs((actual - predicted) / actual)) * 100`

Target threshold: `< 10%`.

## 3. Match outcome probability

`stats-service` uses an Elo-like probability with form adjustment:

`P(team_a) = 1 / (1 + 10^(-(rating_gap + form_delta * 40)/400))`

## 4. Cheat risk detection

For selected metrics (e.g., headshot%), service computes z-score of last point against the sample distribution.

- risk score = `abs(last - mean) / std`
- suspicious when score >= threshold (default 3.2)

## 5. Async stats processing

`/stats/collect/start` spawns an async job that appends metric events without blocking API response.

## 6. Access model

RBAC roles: `admin`, `organizer`, `captain`, `player`, `spectator`.

Examples:

- `organizer` can `match:manage`, `stream:manage`, `notification:send`
- `spectator` can `stream:read`, `stats:read`, `interaction:vote`
