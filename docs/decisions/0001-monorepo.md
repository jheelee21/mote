# 0001 — Single monorepo

- **Status:** accepted
- **Date:** 2026-11-16

## Context

Mote ships as one installer containing a React/Tauri frontend and a bundled Python sidecar. The sidecar has no other clients, and most features change both sides (schema, route, generated types, UI).

## Decision

Keep the desktop app, backend, generated API types, research and tooling in one repository.

## Consequences

- One PR can change a feature end to end; any commit is a known-good frontend/backend pair.
- Generated API types are produced from a sibling folder with no publishing step.
- One CI and release workflow builds the sidecar and the installers together.
- Two toolchains (uv, pnpm) live side by side; CI uses path filters to avoid running everything on every change.
- If a component becomes useful on its own (e.g. a `mote-core` library or a Lightroom plugin), split it out then.
