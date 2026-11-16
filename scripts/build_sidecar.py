"""Build the Python sidecar into a single executable for Tauri.

Tauri expects external binaries named `<name>-<target-triple>[.exe]` in
`apps/desktop/src-tauri/binaries/`. Run from the repo root:

    cd backend && uv run python ../scripts/build_sidecar.py
"""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
OUT_DIR = ROOT / "apps" / "desktop" / "src-tauri" / "binaries"
NAME = "mote-sidecar"


def target_triple() -> str:
    try:
        out = subprocess.run(["rustc", "-vV"], capture_output=True, text=True, check=True).stdout
    except (FileNotFoundError, subprocess.CalledProcessError):
        sys.exit("rustc not found: install the Rust toolchain to determine the target triple")
    for line in out.splitlines():
        if line.startswith("host:"):
            return line.split(":", 1)[1].strip()
    sys.exit("could not determine target triple from `rustc -vV`")


def main() -> None:
    triple = target_triple()
    ext = ".exe" if platform.system() == "Windows" else ""
    subprocess.run(
        [
            sys.executable, "-m", "PyInstaller",
            "--onefile",
            "--name", NAME,
            "--distpath", str(BACKEND / "dist"),
            "--workpath", str(BACKEND / "build"),
            str(BACKEND / "src" / "mote" / "__main__.py"),
        ],
        check=True,
        cwd=BACKEND,
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    dest = OUT_DIR / f"{NAME}-{triple}{ext}"
    shutil.copy2(BACKEND / "dist" / f"{NAME}{ext}", dest)
    print(f"Sidecar written to {dest}")


if __name__ == "__main__":
    main()
