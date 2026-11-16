import { open } from "@tauri-apps/plugin-dialog";

import { useAddLibrary, useLibraries } from "../api/hooks";

export function StoriesScreen() {
  const libraries = useLibraries();
  const addLibrary = useAddLibrary();

  async function pickFolder() {
    const selected = await open({ directory: true, multiple: false, title: "Add a photo folder" });
    if (typeof selected === "string") addLibrary.mutate(selected);
  }

  const hasLibraries = (libraries.data?.length ?? 0) > 0;

  return (
    <>
      <header className="page-header">
        <div>
          <h1>Stories</h1>
          <p className="muted">
            {hasLibraries
              ? "Themes will appear here once indexing and clustering are built."
              : "Add a folder of photos and Mote will look for the stories in it."}
          </p>
        </div>
        <button type="button" className="btn-primary" onClick={pickFolder}>
          Add folder
        </button>
      </header>

      {addLibrary.isError && (
        <p role="alert" className="error">
          {String(addLibrary.error)}
        </p>
      )}

      {!hasLibraries && (
        <div className="empty">
          <p>Your photos stay where they are. Mote only reads them, on this computer.</p>
        </div>
      )}
    </>
  );
}
