# Architecture

## Overview

eSports Arena follows a domain-oriented microservice architecture with a gateway orchestration layer. The platform covers the full tournament lifecycle:

`registration -> scheduling -> match start -> stream launch -> fan notify -> stats collection -> result publishing`

## Service responsibilities

- `tournament-service`: tournament entities, discipline catalog, team registration to tournaments
- `team-service`: teams, player transfers, role-based access, 2FA auth
- `match-service`: match planning, status transitions (`scheduled/live/finished`), score updates
- `streaming-service`: stream creation, stream node balancing, external integrations
- `stats-service`: live event ingestion, async collection jobs, KPI and ML-like estimations
- `interaction-service`: fan polls (MVP/predictions), vote counting, interaction intent parser
- `notification-service`: fan and operational notifications
- `api-gateway`: cross-service workflow orchestration and dashboard aggregation

## Data flow for `start-match`

1. Gateway validates `match:manage` permission in `team-service`
2. Match metadata is loaded from `match-service`
3. `streaming-service` creates a stream and selects a least-loaded node
4. `notification-service` pushes fan notification with stream link
5. `match-service` moves match to `live`
6. `stats-service` launches async statistics collection job

## Performance strategy

- Horizontal microservice scaling via stateless FastAPI containers
- Redis cache for hot dashboard/KPI data
- Async collection task for stats events
- Stream-node balancing by live load ratio
- Dedicated analytics service for MAPE and anomaly/cheat checks
