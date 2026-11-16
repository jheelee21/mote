import type { Job } from "../api/types";

export function IndexingStatus({ jobs }: { jobs: Job[] }) {
  const active = jobs.find((j) => j.status === "running" || j.status === "queued");
  const pct = active && active.total > 0 ? Math.round((active.progress / active.total) * 100) : null;

  return (
    <div className="indexing" aria-live="polite">
      <div className="indexing-head">
        <span>{active ? "Indexing on this computer" : "Up to date"}</span>
        {pct !== null && <span className="muted">{pct}%</span>}
      </div>
      <div className="bar">
        <div className="bar-fill" style={{ width: `${pct ?? (active ? 15 : 100)}%` }} />
      </div>
      <span className="muted small">
        {active?.message ?? "Nothing leaves your computer."}
      </span>
    </div>
  );
}
