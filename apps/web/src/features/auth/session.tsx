"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { ApiError, apiDownload, apiFetch, isUUID } from "@/lib/api/client";
import type { components } from "@/lib/api/generated";

export type Identity = components["schemas"]["CurrentUserResponse"];
type LoginResponse = components["schemas"]["TokenResponse"];
export type Role = Identity["role"];
type Session = { user: Identity; expiresAt: number; generation: number };
type EndReason = "expired" | "invalid" | null;
type SessionContext = {
  session: Session | null;
  signingIn: boolean;
  reason: EndReason;
  signIn: (alias: string) => Promise<Identity>;
  signOut: () => void;
  request: <T>(path: string, options?: RequestInit) => Promise<T>;
  download: (
    path: string,
    signal?: AbortSignal,
  ) => Promise<{ blob: Blob; filename: string }>;
};
const Context = createContext<SessionContext | null>(null);
const roles: Role[] = [
  "INSTITUTION_ADMIN",
  "AICTE_OFFICER",
  "AICTE_MANAGER",
  "AUTHORIZED_VERIFIER",
];

export function homeFor(role: Role): string {
  return role === "INSTITUTION_ADMIN"
    ? "/institution"
    : role === "AUTHORIZED_VERIFIER"
      ? "/access-denied"
      : "/aicte";
}

export function SessionProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: { retry: false, staleTime: 0, gcTime: 60_000 },
          mutations: { retry: false },
        },
      }),
  );
  const [session, setSession] = useState<Session | null>(null);
  const [signingIn, setSigningIn] = useState(false);
  const [reason, setReason] = useState<EndReason>(null);
  const token = useRef<string | null>(null);
  const expiresAt = useRef(0);
  const generation = useRef(0);
  const login = useRef<AbortController | null>(null);
  const requests = useRef(new Set<AbortController>());

  const clear = useCallback(
    (why: EndReason) => {
      generation.current += 1;
      token.current = null;
      expiresAt.current = 0;
      login.current?.abort();
      login.current = null;
      for (const controller of requests.current) controller.abort();
      requests.current.clear();
      void queryClient.cancelQueries();
      queryClient.clear();
      setSession(null);
      setSigningIn(false);
      setReason(why);
    },
    [queryClient],
  );

  const end = useCallback(
    (why: EndReason) => {
      clear(why);
      router.replace("/login");
    },
    [clear, router],
  );

  useEffect(() => {
    if (!session) return;
    const check = () => {
      if (Date.now() >= session.expiresAt) end("expired");
    };
    const timer = window.setTimeout(
      check,
      Math.max(0, session.expiresAt - Date.now()),
    );
    document.addEventListener("visibilitychange", check);
    return () => {
      window.clearTimeout(timer);
      document.removeEventListener("visibilitychange", check);
    };
  }, [session, end]);

  useEffect(() => {
    const active = requests.current;
    return () => {
      login.current?.abort();
      for (const controller of active) controller.abort();
    };
  }, []);

  const signIn = useCallback(
    async (alias: string) => {
      clear(null);
      const attempt = generation.current;
      const controller = new AbortController();
      login.current = controller;
      setSigningIn(true);
      try {
        const credentials = await apiFetch<LoginResponse>("/auth/demo-login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ demo_alias: alias }),
          signal: controller.signal,
        });
        if (
          !credentials ||
          typeof credentials.access_token !== "string" ||
          !credentials.access_token ||
          credentials.token_type !== "bearer" ||
          credentials.demo_mode !== true ||
          !Number.isInteger(credentials.expires_in) ||
          credentials.expires_in <= 0 ||
          credentials.expires_in > 3600
        ) {
          throw new ApiError(0, "INVALID_RESPONSE");
        }
        const expiry = Date.now() + credentials.expires_in * 1000;
        const user = await apiFetch<Identity>(
          "/me",
          { signal: controller.signal },
          credentials.access_token,
        );
        if (
          !user ||
          !isUUID(user.id) ||
          !roles.includes(user.role) ||
          user.demo_mode !== true ||
          (user.role === "INSTITUTION_ADMIN" && !isUUID(user.institution_id)) ||
          (user.institution_id !== null && !isUUID(user.institution_id))
        )
          throw new ApiError(0, "INVALID_RESPONSE");
        if (generation.current !== attempt || controller.signal.aborted)
          throw new DOMException("Session ended", "AbortError");
        if (Date.now() >= expiry) throw new ApiError(401, "SESSION_EXPIRED");
        token.current = credentials.access_token;
        expiresAt.current = expiry;
        login.current = null;
        setSession({ user, expiresAt: expiry, generation: attempt });
        return user;
      } finally {
        if (generation.current === attempt) setSigningIn(false);
      }
    },
    [clear],
  );

  const request = useCallback(
    async <T,>(path: string, options: RequestInit = {}): Promise<T> => {
      const activeToken = token.current;
      const attempt = generation.current;
      if (!activeToken) throw new ApiError(401, "NOT_AUTHENTICATED");
      if (Date.now() >= expiresAt.current) {
        end("expired");
        throw new ApiError(401, "SESSION_EXPIRED");
      }
      const controller = new AbortController();
      const abort = () => controller.abort();
      if (options.signal?.aborted) abort();
      options.signal?.addEventListener("abort", abort, { once: true });
      requests.current.add(controller);
      try {
        const result = await apiFetch<T>(
          path,
          { ...options, signal: controller.signal },
          activeToken,
        );
        if (attempt !== generation.current)
          throw new DOMException("Session ended", "AbortError");
        return result;
      } catch (error) {
        if (
          attempt === generation.current &&
          error instanceof ApiError &&
          error.status === 401
        )
          end(error.code === "SESSION_EXPIRED" ? "expired" : "invalid");
        throw error;
      } finally {
        options.signal?.removeEventListener("abort", abort);
        requests.current.delete(controller);
      }
    },
    [end],
  );

  const download = useCallback(
    async (path: string, signal?: AbortSignal) => {
      const activeToken = token.current;
      const attempt = generation.current;
      if (!activeToken) throw new ApiError(401, "NOT_AUTHENTICATED");
      if (Date.now() >= expiresAt.current) {
        end("expired");
        throw new ApiError(401, "SESSION_EXPIRED");
      }
      const controller = new AbortController();
      const abort = () => controller.abort();
      if (signal?.aborted) abort();
      signal?.addEventListener("abort", abort, { once: true });
      requests.current.add(controller);
      try {
        const result = await apiDownload(path, activeToken, controller.signal);
        if (attempt !== generation.current)
          throw new DOMException("Session ended", "AbortError");
        return result;
      } catch (error) {
        if (
          attempt === generation.current &&
          error instanceof ApiError &&
          error.status === 401
        )
          end(error.code === "SESSION_EXPIRED" ? "expired" : "invalid");
        throw error;
      } finally {
        signal?.removeEventListener("abort", abort);
        requests.current.delete(controller);
      }
    },
    [end],
  );

  return (
    <QueryClientProvider client={queryClient}>
      <Context.Provider
        value={{
          session,
          signingIn,
          reason,
          signIn,
          signOut: () => end(null),
          request,
          download,
        }}
      >
        {children}
      </Context.Provider>
    </QueryClientProvider>
  );
}

export function useSession() {
  const context = useContext(Context);
  if (!context) throw new Error("SessionProvider is required");
  return context;
}
