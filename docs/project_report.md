# Project Report: eSports Arena

## Goal

Build a secure and scalable platform for online esports tournaments with orchestration of match lifecycle, streaming, analytics, and fan engagement.

## Implemented core functionality

- Tournament creation and team registration
- Team/player management with transfer operations
- Match scheduling and state transitions
- End-to-end workflow: `start-match` and `finish-match`
- Stream session creation and node balancing
- Fan notifications and interaction polls
- KPI dashboard and statistics APIs
- 2FA and role-based access checks

## Quality and performance alignment

- Stream delay target monitored in KPI (`target_stream_delay_sec = 10`)
- Stats refresh target monitored in KPI (`target_stats_refresh_sec = 2`)
- ETA MAPE endpoint available for model quality control
- Viewer capacity target fixed at 100,000

## Tests and validation

- Unit tests for analytics, interaction parsing, security helpers
- Integration tests for auth, match-stream pipeline, poll and prediction flow
- Load test stubs for Locust and k6

## Delivered artifacts

- Source code with Dockerfiles per service
- `docker-compose.yml` for local deployment
- Tests (`tests/unit`, `tests/integration`, `tests/load`)
- CI templates (`.github/workflows`)
- Documentation in `docs/`
- Sample dataset generator (`scripts/generate_sample_data.py`, 12k events)
