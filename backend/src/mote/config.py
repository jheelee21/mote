"""Runtime settings for the sidecar."""

from __future__ import annotations

import os
import platform
from dataclasses import dataclass, field
from pathlib import Path


def default_data_dir() -> Path:
    """Per-user app data directory, matching where Tauri stores app data."""
    system = platform.system()
    home = Path.home()
    if system == "Darwin":
        return home / "Library" / "Application Support" / "app.mote"
    if system == "Windows":
        return Path(os.environ.get("APPDATA", home / "AppData" / "Roaming")) / "app.mote"
    return Path(os.environ.get("XDG_DATA_HOME", home / ".local" / "share")) / "app.mote"


@dataclass(frozen=True)
class Settings:
    host: str = "127.0.0.1"
    port: int = 8765
    token: str | None = None
    data_dir: Path = field(default_factory=default_data_dir)
    embedder: str = "dummy"

    @property
    def db_path(self) -> Path:
        return self.data_dir / "mote.sqlite"

    @property
    def thumbs_dir(self) -> Path:
        return self.data_dir / "thumbs"

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.thumbs_dir.mkdir(parents=True, exist_ok=True)
