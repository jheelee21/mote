import type { Health } from "@mote/api-types";

import type { Job, Library } from "./types";

export interface BackendInfo {
  url: string;
  token: string;
}

let backendPromise: Promise<BackendInfo> | null = null;

/**
 * Where the API lives. In plain-browser dev (`pnpm vite` with VITE_MOTE_API set)
 * we use env vars; inside Tauri we ask the Rust side, which started the sidecar.
 */
export function resolveBackend(): Promise<BackendInfo> {
  if (!backendPromise) {
    const envUrl = import.meta.env.VITE_MOTE_API as string | undefined;
    if (envUrl) {
      backendPromise = Promise.resolve({
        url: envUrl,
        token: (import.meta.env.VITE_MOTE_TOKEN as string | undefined) ?? "dev",
      });
    } else {
      backendPromise = import("@tauri-apps/api/core").then(({ invoke }) =>
        invoke<BackendInfo>("backend_info"),
      );
    }
  }
  return backendPromise;
}

export function buildUrl(base: string, path: string): string {
  return `${base.replace(/\/+$/, "")}/${path.replace(/^\/+/, "")}`;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

export async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const { url, token } = await resolveBackend();
  const res = await fetch(buildUrl(url, path), {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...init.headers,
    },
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail ?? detail;
    } catch {
      /* body was not JSON */
    }
    throw new ApiError(res.status, detail);
  }
  return res.status === 204 ? (undefined as T) : ((await res.json()) as T);
}

export const api = {
  health: () => request<Health>("/health"),
  libraries: () => request<Library[]>("/libraries"),
  addLibrary: (rootPath: string) =>
    request<Library>("/libraries", {
      method: "POST",
      body: JSON.stringify({ root_path: rootPath }),
    }),
  scanLibrary: (id: number) => request<Job>(`/libraries/${id}/scan`, { method: "POST" }),
  jobs: () => request<Job[]>("/jobs"),
};
