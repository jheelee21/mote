// Temporary hand-written types for endpoints not yet in the generated schema.
// Replace with imports from "@mote/api-types" after the first `pnpm gen:api`.

export interface Library {
  id: number;
  root_path: string;
  name: string;
  added_at: string;
  last_scan_at: string | null;
  photo_count: number;
}

export type JobStatus = "queued" | "running" | "done" | "failed" | "cancelled";

export interface Job {
  id: string;
  type: string;
  status: JobStatus;
  progress: number;
  total: number;
  message: string | null;
  error: string | null;
}
