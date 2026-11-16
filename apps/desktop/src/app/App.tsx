import { useState } from "react";

import { useHealth } from "../api/hooks";
import { Sidebar, type Screen } from "../components/Sidebar";
import { AllPhotosScreen } from "../screens/AllPhotos";
import { StoriesScreen } from "../screens/Stories";

export function App() {
  const [screen, setScreen] = useState<Screen>("stories");
  const health = useHealth();

  if (health.isPending) {
    return <div className="splash">Starting Mote…</div>;
  }
  if (health.isError) {
    return (
      <div className="splash">
        <p>Mote's engine didn't start.</p>
        <p className="muted">{String(health.error)}</p>
      </div>
    );
  }

  return (
    <div className="shell">
      <Sidebar current={screen} onNavigate={setScreen} />
      <main className="content">
        {screen === "stories" && <StoriesScreen />}
        {screen === "photos" && <AllPhotosScreen />}
        {(screen === "series" || screen === "exports") && (
          <p className="muted">Coming soon.</p>
        )}
      </main>
    </div>
  );
}
