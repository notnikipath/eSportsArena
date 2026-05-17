# Demo Script

1. Start platform:

```bash
docker compose up --build -d
```

2. Open dashboard:

- `http://localhost:5182`

3. Verify backend health:

- `http://localhost:8680/health`
- `http://localhost:8680/services/health`

4. Run scripted workflow:

```bash
python scripts/demo_pipeline.py
```

5. Show in demo:

- successful 2FA auth
- match status changes from `scheduled` -> `live` -> `finished`
- stream session generated with URL and node
- notification history growth
- KPI and stats events update on dashboard
