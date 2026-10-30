"use client";

import {
  useQuery,
  type UseQueryOptions,
  type UseQueryResult,
} from "@tanstack/react-query";
import { useCallback, useState } from "react";
import { useSession } from "@/features/auth/session";

/**
 * The private per-session scope every authenticated query key starts with.
 * A session generation change invalidates everything under it.
 */
export function useScope(...parts: unknown[]): unknown[] {
  const { session } = useSession();
  return ["private", session?.generation, session?.user.id, ...parts];
}

type ApiQueryOptions<T> = Omit<
  UseQueryOptions<T, Error, T, readonly unknown[]>,
  "queryKey" | "queryFn" | "enabled"
> & { enabled?: boolean };

/**
 * `useQuery` over an authenticated GET: the key is [scope, path], the query
 * runs only with a live session, and a null/empty path disables the query.
 * Outliers that need fan-out (`useQueries`), infinite scroll or chained
 * option data stay on hand-written `useQuery`.
 */
export function useApiQuery<T>(
  scope: unknown[],
  path: string | null,
  options: ApiQueryOptions<T> = {},
): UseQueryResult<T> {
  const { session, request } = useSession();
  const { enabled = true, ...rest } = options;
  return useQuery<T>({
    ...rest,
    queryKey: [...scope, path],
    enabled: Boolean(session) && Boolean(path) && enabled,
    queryFn: ({ signal }) => request<T>(path as string, { signal }),
  });
}

/**
 * Draft/Apply/Clear filter state shared by list pages: the draft edits freely,
 * validation errors block apply, and applied filters drive the queries.
 */
export function useDraftFilters<F>(
  initial: F,
  validate: (draft: F) => string | null,
  {
    onApplied,
    onCleared,
  }: { onApplied?: (filters: F) => void; onCleared?: () => void } = {},
) {
  const [draft, setDraft] = useState(initial);
  const [filters, setFilters] = useState(initial);
  const [error, setError] = useState<string | null>(null);
  const apply = useCallback(() => {
    const problem = validate(draft);
    if (problem) {
      setError(problem);
      return;
    }
    setError(null);
    setFilters(draft);
    onApplied?.(draft);
  }, [draft, validate, onApplied]);
  const clear = useCallback(() => {
    setDraft(initial);
    setFilters(initial);
    setError(null);
    onCleared?.();
    // `initial` is a fresh object per render at call sites; it is a value, not
    // a dependency contract.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [onCleared]);
  return { draft, setDraft, filters, error, apply, clear };
}

/** Live-update filter state: every edit bumps the page back to 1. */
export function useFilterState<F extends object>(
  noFilters: F,
  resetPage: () => void,
) {
  const [filters, setFilters] = useState<F>(noFilters);
  const update = useCallback(
    <K extends keyof F>(key: K, value: F[K]) => {
      setFilters((current) => ({ ...current, [key]: value }));
      resetPage();
    },
    [resetPage],
  );
  const reset = useCallback(() => {
    setFilters(noFilters);
    resetPage();
  }, [noFilters, resetPage]);
  return { filters, setFilters, update, reset };
}

/** Copy-to-clipboard feedback: `copied` clears itself after a moment. */
export function useCopy(resetMs = 2000) {
  const [copied, setCopied] = useState(false);
  const copy = useCallback(
    (text: string) => {
      const done = navigator.clipboard
        ?.writeText(text)
        .then(() => true)
        .catch(() => false);
      void done.then((ok) => {
        setCopied(ok);
        if (ok) window.setTimeout(() => setCopied(false), resetMs);
      });
      return done;
    },
    [resetMs],
  );
  return { copied, copy };
}
