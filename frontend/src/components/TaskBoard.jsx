import React from "react";

export function TaskBoard({ matches }) {
  if (!matches?.length) {
    return <div className="empty-board">No matches scheduled yet.</div>;
  }

  const byStatus = matches.reduce((acc, match) => {
    const status = match.status || "unknown";
    if (!acc[status]) {
      acc[status] = [];
    }
    acc[status].push(match);
    return acc;
  }, {});

  return (
    <section className="room-grid">
      {Object.entries(byStatus).map(([status, items]) => (
        <article className="room-card" key={status}>
          <div className="room-head">
            <p className="module-kicker">Match Status</p>
            <h3>{status}</h3>
          </div>
          <div className="stack-list">
            {items.map((match) => (
              <div className="stack-item" key={match.match_id}>
                <div>
                  <p className="stack-title">{match.team_a_id} vs {match.team_b_id}</p>
                  <p className="stack-sub">{match.round_label}</p>
                </div>
                <span>{new Date(match.scheduled_at).toLocaleTimeString()}</span>
              </div>
            ))}
          </div>
        </article>
      ))}
    </section>
  );
}
