# API Summary

## Gateway

- `GET /health`
- `GET /services/health`
- `POST /auth/challenge/start`
- `POST /auth/challenge/verify`
- `POST /auth/verify`
- `POST /workflow/start-match`
- `POST /workflow/finish-match`
- `GET /dashboard/{arena_id}/{user_id}`

## Tournament service

- `GET /health`
- `GET /disciplines`
- `GET /tournaments`
- `GET /tournaments/{tournament_id}`
- `POST /tournaments`
- `POST /tournaments/{tournament_id}/register-team`

## Team service

- `GET /health`
- `POST /auth/challenge/start`
- `POST /auth/challenge/verify`
- `POST /access/check`
- `GET /users`
- `GET /teams`
- `GET /teams/{team_id}`
- `POST /teams`
- `POST /teams/{team_id}/transfers`

## Match service

- `GET /health`
- `GET /matches`
- `GET /matches/{match_id}`
- `POST /matches`
- `POST /matches/{match_id}/status`
- `POST /matches/{match_id}/result/ingest`

## Streaming service

- `GET /health`
- `POST /streams/create`
- `GET /streams`
- `GET /streams/nodes`
- `POST /integrations/twitch/connect`
- `POST /integrations/youtube/connect`
- `POST /integrations/game-api/sync`
- `GET /integrations/history`

## Stats service

- `GET /health`
- `POST /stats/events`
- `POST /stats/collect/start`
- `GET /stats/match/{match_id}`
- `GET /stats/kpi`
- `POST /stats/eta/mape`
- `POST /stats/predict/outcome`
- `POST /stats/cheat/detect`
- `GET /stats/anomalies`

## Interaction service

- `GET /health`
- `POST /interaction/parse`
- `POST /interaction/polls`
- `GET /interaction/polls`
- `GET /interaction/polls/{poll_id}`
- `POST /interaction/votes`
- `GET /interaction/polls/{poll_id}/results`
- `POST /interaction/mvp/recommend`
