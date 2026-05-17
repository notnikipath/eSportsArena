# Deployment Guide

## Local prerequisites

- Docker Desktop 4.x+
- Docker Compose v2+
- Python 3.11+ (for local scripts/tests)

## Start

```bash
cd d:\Шарага\Кинжибаев\task_12_esportsarena
docker compose up --build -d
```

## Stop

```bash
docker compose down
```

## Check health

```bash
curl http://localhost:8680/health
curl http://localhost:8680/services/health
```

## Main URLs

- Frontend: `http://localhost:5182`
- Gateway Swagger: `http://localhost:8680/docs`
- RabbitMQ UI: `http://localhost:15683`

## Smoke workflow

```bash
python scripts/demo_pipeline.py
```

This script executes:

- 2FA challenge start/verify
- match start workflow
- match finish workflow

## CI/CD notes

- Unit/integration tests run with `pytest`
- Static checks run with `ruff`
- Container image build is validated with `docker compose config` + compose build
