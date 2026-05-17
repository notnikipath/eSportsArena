# Presentation Outline

1. Problem context
- Tournament operations are fragmented across tools, creating delays in scheduling, streaming, and reporting.

2. Solution
- eSports Arena unifies tournament operations into an event-driven microservice platform.

3. Architecture
- Gateway + 7 domain services + frontend dashboard
- Async stats and integration layer

4. Live demo
- 2FA login
- Start match workflow
- Stream creation + fan notification
- KPI and stats updates

5. Metrics and targets
- stream delay < 10 sec
- stats refresh < 2 sec
- capacity target 100,000 concurrent viewers

6. Roadmap
- anti-cheat model training on historical logs
- bookmaker/odds integration
- mobile fan app and push segmentation
