"""Command-line entry point: `mote serve` and `mote openapi`."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from mote.config import Settings, default_data_dir


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="mote", description="Mote backend sidecar")
    sub = p.add_subparsers(dest="command", required=True)

    serve = sub.add_parser("serve", help="run the API server")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)
    serve.add_argument("--token", default=None, help="bearer token required on every request")
    serve.add_argument("--data-dir", type=Path, default=default_data_dir())
    serve.add_argument("--embedder", default="dummy", help="embedder id from the model registry")

    sub.add_parser("openapi", help="print the OpenAPI schema as JSON")
    return p


def main(argv: list[str] | None = None) -> None:
    args = _parser().parse_args(argv)

    if args.command == "openapi":
        from mote.main import create_app

        app = create_app(Settings(data_dir=Path(".mote-openapi-tmp")), init_storage=False)
        json.dump(app.openapi(), sys.stdout, indent=2)
        sys.stdout.write("\n")
        return

    if args.command == "serve":
        import uvicorn

        from mote.main import create_app

        settings = Settings(
            host=args.host,
            port=args.port,
            token=args.token,
            data_dir=args.data_dir,
            embedder=args.embedder,
        )
        if settings.host not in ("127.0.0.1", "localhost", "::1"):
            sys.exit("Refusing to bind to a non-loopback address: Mote is local-only.")
        uvicorn.run(create_app(settings), host=settings.host, port=settings.port, log_level="info")
