# eSports Arena

eSports Arena is a microservice platform for organizing online esports tournaments with full workflow support: team onboarding, match lifecycle, streaming, fan interaction, and statistics.

## Services

- `api-gateway` - orchestration and aggregated dashboard
- `tournament-service` - tournament setup and team registration
- `team-service` - teams, players, transfers, RBAC, 2FA auth
- `match-service` - match scheduling and status updates
- `streaming-service` - stream sessions, video balancing, Twitch/YouTube/game API integration
- `stats-service` - live stats, async collection, ETA MAPE, cheat risk detection
- `interaction-service` - polls, votes, fan interaction parsing
- `notification-service` - fan and operational notifications
- `frontend` - operational dashboard

## Implemented optional improvements (6)

1. Match outcome prediction (`/stats/predict/outcome`)
2. Cheater detection (`/stats/cheat/detect`)
3. Twitch and YouTube integrations
4. Video server load balancing (`/streams/create` node selection)
5. Cached statistics KPI (`TTLCache` in `stats-service`)
6. Asynchronous log/stat processing (`/stats/collect/start`)

## Stack

- Backend: Python FastAPI microservices
- Data: PostgreSQL, Redis, InfluxDB
- Queue: RabbitMQ
- Streaming: HLS/WebRTC-ready integration layer
- Frontend: React + Vite

## Run locally

```bash
cd 'your/project/folder'
docker compose up --build -d
```

## Endpoints

- Frontend: `http://localhost:5182`
- Gateway health: `http://localhost:8680/health`
- Services health: `http://localhost:8680/services/health`
- Swagger: `http://localhost:8680/docs`

## Validation

```bash
python -m ruff check .
python -m pytest -q
docker compose config
```

## Demo workflow

```bash
python scripts/demo_pipeline.py
```

## Sample data

```bash
python scripts/generate_sample_data.py
```

Output file: `data/samples/esports_events.json`
