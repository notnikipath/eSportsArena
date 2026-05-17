import React, { useEffect, useMemo, useState } from "react";

import { KpiCard } from "../components/KpiCard";
import { TaskBoard } from "../components/TaskBoard";

const gatewayUrl = import.meta.env.VITE_API_GATEWAY_URL || "http://localhost:8680";

const emptyDashboard = {
  arena_id: "ARENA-DEMO",
  user_id: "USR-ORG-1",
  tournaments: { items: [] },
  matches: { items: [] },
  teams: { items: [] },
  users: { items: [] },
  streams: { items: [] },
  integrations: { items: [] },
  polls: { items: [] },
  anomalies: { items: [] },
  notifications: { items: [] },
  kpi: {
    stream_delay_sec: 0,
    target_stream_delay_sec: 10,
    stats_refresh_sec: 0,
    target_stats_refresh_sec: 2,
    availability_pct: 0,
    viewer_capacity_target: 100000,
    events_count: 0,
    cheat_alerts: 0,
  },
};

async function loadDashboard(arenaId, userId) {
  const response = await fetch(`${gatewayUrl}/dashboard/${arenaId}/${userId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch dashboard: ${response.status}`);
  }
  return response.json();
}

async function startMatch(matchId, userId, arenaId) {
  const response = await fetch(`${gatewayUrl}/workflow/start-match`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      match_id: matchId,
      user_id: userId,
      arena_id: arenaId,
      actor_role: "organizer",
      provider: "hls",
    }),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Start match failed: ${response.status} ${detail}`);
  }
  return response.json();
}

async function finishMatch(matchId, userId) {
  const response = await fetch(`${gatewayUrl}/workflow/finish-match`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      match_id: matchId,
      user_id: userId,
      score_team_a: 2,
      score_team_b: 1,
      actor_role: "organizer",
    }),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Finish match failed: ${response.status} ${detail}`);
  }
  return response.json();
}

export function DashboardPage() {
  const [arenaId, setArenaId] = useState("ARENA-DEMO");
  const [userId, setUserId] = useState("USR-ORG-1");
  const [theme, setTheme] = useState("light");
  const [status, setStatus] = useState("loading");
  const [error, setError] = useState(null);
  const [dashboard, setDashboard] = useState(emptyDashboard);
  const [lastWorkflow, setLastWorkflow] = useState(null);

  const refresh = async () => {
    try {
      setStatus("loading");
      const payload = await loadDashboard(arenaId, userId);
      setDashboard({ ...emptyDashboard, ...payload });
      setStatus("succeeded");
      setError(null);
    } catch (err) {
      setStatus("failed");
      setError(err.message);
    }
  };

  useEffect(() => {
    refresh();
  }, [arenaId, userId]);

  const runStartMatch = async () => {
    const firstMatch = dashboard.matches?.items?.[0];
    if (!firstMatch) {
      setError("No match available to start.");
      return;
    }
    try {
      const workflow = await startMatch(firstMatch.match_id, userId, arenaId);
      setLastWorkflow(workflow);
      await refresh();
    } catch (err) {
      setError(err.message);
    }
  };

  const runFinishMatch = async () => {
    const liveMatch = dashboard.matches?.items?.find((item) => item.status === "live") || dashboard.matches?.items?.[0];
    if (!liveMatch) {
      setError("No match available to finish.");
      return;
    }
    try {
      await finishMatch(liveMatch.match_id, userId);
      await refresh();
    } catch (err) {
      setError(err.message);
    }
  };

  const statusLabel = useMemo(() => {
    if (status === "loading") {
      return "loading";
    }
    if (status === "failed") {
      return "fallback";
    }
    return "live";
  }, [status]);

  const matches = dashboard.matches?.items || [];
  const polls = dashboard.polls?.items || [];
  const streams = dashboard.streams?.items || [];
  const notifications = dashboard.notifications?.items || [];

  return (
    <div className={`app theme-${theme}`}>
      <div className="background-orb orb-a" />
      <div className="background-orb orb-b" />

      <header className="hero">
        <div className="hero-copy">
          <p className="eyebrow">eSports Arena</p>
          <h1>Online tournament control center for matches, streams, stats, and fan interaction.</h1>
          <p className="sub">
            Run the full match workflow: schedule and start games, launch streams, collect live statistics,
            and trigger fan notifications in one place.
          </p>
          <div className="hero-badges">
            <span>Twitch/YouTube connectors</span>
            <span>Video load balancing</span>
            <span>Cheat risk detection</span>
            <span>MVP and prediction polls</span>
          </div>
        </div>

        <div className="hero-panel">
          <label>
            Arena ID
            <input value={arenaId} onChange={(event) => setArenaId(event.target.value)} placeholder="ARENA-DEMO" />
          </label>
          <label>
            User ID
            <input value={userId} onChange={(event) => setUserId(event.target.value)} placeholder="USR-ORG-1" />
          </label>
          <div className="hero-actions">
            <button onClick={runStartMatch}>Start Match</button>
            <button onClick={runFinishMatch}>Finish Match</button>
            <button className="ghost" onClick={refresh}>Refresh</button>
            <button className="ghost" onClick={() => setTheme((current) => (current === "light" ? "dark" : "light"))}>Theme</button>
          </div>
          <p className="status-line">Status: {statusLabel}</p>
        </div>
      </header>

      <section className="kpi-grid">
        <KpiCard
          title="Stream Delay"
          value={`${Number(dashboard.kpi?.stream_delay_sec || 0).toFixed(2)} sec`}
          target={`Target < ${dashboard.kpi?.target_stream_delay_sec || 10} sec`}
          ok={Number(dashboard.kpi?.stream_delay_sec || 999) <= Number(dashboard.kpi?.target_stream_delay_sec || 10)}
        />
        <KpiCard
          title="Stats Refresh"
          value={`${Number(dashboard.kpi?.stats_refresh_sec || 0).toFixed(2)} sec`}
          target={`Target < ${dashboard.kpi?.target_stats_refresh_sec || 2} sec`}
          ok={Number(dashboard.kpi?.stats_refresh_sec || 999) <= Number(dashboard.kpi?.target_stats_refresh_sec || 2)}
        />
        <KpiCard
          title="Availability"
          value={`${Number(dashboard.kpi?.availability_pct || 0).toFixed(2)}%`}
          target="Target 99.9%"
          ok={Number(dashboard.kpi?.availability_pct || 0) >= 99.9}
        />
        <KpiCard
          title="Cheat Alerts"
          value={`${Number(dashboard.kpi?.cheat_alerts || 0)}`}
          target="Should stay near zero"
          ok={Number(dashboard.kpi?.cheat_alerts || 0) <= 1}
        />
      </section>

      {error ? <div className="error-banner">{error}</div> : null}

      <section className="content-grid">
        <article className="panel panel-featured">
          <div className="panel-head compact">
            <div>
              <p className="section-kicker">Matches</p>
              <h2>Live tournament board</h2>
            </div>
            <span className="pill">{matches.length} matches</span>
          </div>
          <div className="metrics-row">
            <div>
              <strong>{dashboard.tournaments?.count || 0}</strong>
              <span>tournaments</span>
            </div>
            <div>
              <strong>{dashboard.teams?.count || 0}</strong>
              <span>teams</span>
            </div>
            <div>
              <strong>{dashboard.users?.count || 0}</strong>
              <span>accounts</span>
            </div>
            <div>
              <strong>{dashboard.kpi?.viewer_capacity_target || 0}</strong>
              <span>viewer capacity target</span>
            </div>
          </div>
          <TaskBoard matches={matches} />
        </article>

        <article className="panel">
          <div className="panel-head compact">
            <div>
              <p className="section-kicker">Streams</p>
              <h2>Broadcast sessions</h2>
            </div>
            <span className="pill accent">{streams.length} active</span>
          </div>
          <div className="stack-list">
            {streams.length ? (
              streams.map((stream) => (
                <div className="stack-item" key={stream.stream_id}>
                  <div>
                    <p className="stack-title">{stream.match_id}</p>
                    <p className="stack-sub">{stream.provider} • {stream.delay_sec}s delay</p>
                  </div>
                  <span>{stream.status}</span>
                </div>
              ))
            ) : (
              <div className="empty-board">No streams launched yet.</div>
            )}
          </div>
        </article>

        <article className="panel">
          <div className="panel-head compact">
            <div>
              <p className="section-kicker">Fan Polls</p>
              <h2>MVP and predictions</h2>
            </div>
            <span className="pill">{polls.length}</span>
          </div>
          <div className="stack-list">
            {polls.length ? (
              polls.map((poll) => (
                <div className="stack-item" key={poll.poll_id}>
                  <div>
                    <p className="stack-title">{poll.question}</p>
                    <p className="stack-sub">{poll.vote_type}</p>
                  </div>
                  <span>{poll.status}</span>
                </div>
              ))
            ) : (
              <div className="empty-board">No polls created yet.</div>
            )}
          </div>
        </article>

        <article className="panel">
          <div className="panel-head compact">
            <div>
              <p className="section-kicker">Integrations</p>
              <h2>Streaming and game APIs</h2>
            </div>
            <span className="pill">{dashboard.integrations?.count || 0} syncs</span>
          </div>
          <div className="stack-list">
            {(dashboard.integrations?.items || []).slice(-5).reverse().map((item) => (
              <div className="stack-item" key={item.sync_id}>
                <div>
                  <p className="stack-title">{item.system_name}</p>
                  <p className="stack-sub">{item.status}</p>
                </div>
                <span>{new Date(item.created_at).toLocaleDateString()}</span>
              </div>
            ))}
          </div>
        </article>

        <article className="panel panel-analytics">
          <div className="panel-head compact">
            <div>
              <p className="section-kicker">Workflow</p>
              <h2>Recent operations and notifications</h2>
            </div>
            <span className="pill accent">{dashboard.kpi?.events_count || 0} stats events</span>
          </div>
          <div className="analytics-grid">
            <div>
              <strong>{dashboard.anomalies?.count || 0}</strong>
              <span>anomalies</span>
            </div>
            <div>
              <strong>{notifications.length}</strong>
              <span>notifications</span>
            </div>
            <div>
              <strong>{lastWorkflow?.stream?.provider || "-"}</strong>
              <span>last stream provider</span>
            </div>
            <div>
              <strong>{lastWorkflow?.status_update?.status || "-"}</strong>
              <span>last workflow status</span>
            </div>
          </div>
          <div className="stack-list">
            {notifications.slice(-6).reverse().map((item, idx) => (
              <div className="stack-item" key={`${item.subject}-${idx}`}>
                <div>
                  <p className="stack-title">{item.subject}</p>
                  <p className="stack-sub">{item.body}</p>
                </div>
                <span>{item.severity}</span>
              </div>
            ))}
          </div>
        </article>
      </section>
    </div>
  );
}
