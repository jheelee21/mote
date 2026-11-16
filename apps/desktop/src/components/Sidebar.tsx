import { useJobs, useLibraries } from "../api/hooks";
import { IndexingStatus } from "./IndexingStatus";

export type Screen = "stories" | "photos" | "series" | "exports";

const NAV: { id: Screen; label: string }[] = [
  { id: "stories", label: "Stories" },
  { id: "photos", label: "All photos" },
  { id: "series", label: "Series builder" },
  { id: "exports", label: "Exports" },
];

interface Props {
  current: Screen;
  onNavigate: (screen: Screen) => void;
}

export function Sidebar({ current, onNavigate }: Props) {
  const libraries = useLibraries();
  const jobs = useJobs();

  return (
    <nav className="sidebar" aria-label="Main">
      <div className="brand">
        <svg width="22" height="22" viewBox="0 0 22 22" aria-hidden="true">
          <circle cx="11" cy="11" r="4" fill="var(--accent)" />
          <circle cx="11" cy="11" r="9.5" fill="none" stroke="var(--accent)" strokeOpacity="0.35" />
        </svg>
        <span>mote</span>
      </div>

      <ul className="nav">
        {NAV.map((item) => (
          <li key={item.id}>
            <button
              type="button"
              className="nav-item"
              aria-current={current === item.id ? "page" : undefined}
              onClick={() => onNavigate(item.id)}
            >
              {item.label}
            </button>
          </li>
        ))}
      </ul>

      <section className="libraries">
        <h2 className="eyebrow">Libraries</h2>
        {libraries.data?.length ? (
          libraries.data.map((lib) => (
            <div key={lib.id} className="library-row" title={lib.root_path}>
              <span>{lib.name}</span>
              <span className="muted">{lib.photo_count.toLocaleString()}</span>
            </div>
          ))
        ) : (
          <p className="muted small">No folders yet.</p>
        )}
      </section>

      <IndexingStatus jobs={jobs.data ?? []} />
    </nav>
  );
}
