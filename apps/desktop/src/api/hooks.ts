import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "./client";

export function useHealth() {
  // Poll until the sidecar answers; it can take a few seconds on first launch.
  return useQuery({
    queryKey: ["health"],
    queryFn: api.health,
    retry: 20,
    retryDelay: 500,
  });
}

export function useLibraries(enabled = true) {
  return useQuery({ queryKey: ["libraries"], queryFn: api.libraries, enabled });
}

export function useJobs(enabled = true) {
  return useQuery({
    queryKey: ["jobs"],
    queryFn: api.jobs,
    enabled,
    refetchInterval: (q) =>
      q.state.data?.some((j) => j.status === "running" || j.status === "queued") ? 1000 : false,
  });
}

export function useAddLibrary() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (rootPath: string) => {
      const lib = await api.addLibrary(rootPath);
      await api.scanLibrary(lib.id);
      return lib;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["libraries"] });
      qc.invalidateQueries({ queryKey: ["jobs"] });
    },
  });
}
