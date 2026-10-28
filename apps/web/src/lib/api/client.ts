export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    public readonly requestId?: string,
  ) {
    super(code);
    this.name = "ApiError";
  }
}

export function isUUID(value: unknown): value is string {
  return (
    typeof value === "string" &&
    /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(
      value,
    )
  );
}

function isObject(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object";
}

export function errorMessage(error: unknown): string {
  if (!(error instanceof ApiError))
    return "We couldn’t reach the local API. Check that it is running and try again.";
  switch (error.code) {
    case "DATABASE_UNAVAILABLE":
      return "The database is unavailable. Your information has not been replaced with sample values. Please try again.";
    case "DEMO_LOCAL_ONLY":
      return "Access requires a direct local connection and an approved browser origin.";
    case "NOT_AUTHENTICATED":
      return "This account is unavailable. Check that the local synthetic accounts have been seeded.";
    case "INVALID_RESPONSE":
      return "The API returned an unexpected response. Please check the local setup.";
    default:
      if (error.status === 404)
        return "This resource is unavailable or you do not have access to it.";
      if (error.status === 403)
        return "Your account does not have permission for this action.";
      if (error.status === 422)
        return "The request could not be accepted. Check your selection and try again.";
      return "The service couldn’t complete this request. Please try again.";
  }
}

export function apiBase(): string {
  const base =
    process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000/api/v1";
  const url = new URL(base);
  if (
    !new Set(["localhost", "127.0.0.1", "[::1]"]).has(url.hostname) ||
    !["http:", "https:"].includes(url.protocol) ||
    url.username ||
    url.password ||
    url.search ||
    url.hash ||
    url.pathname.replace(/\/$/, "") !== "/api/v1"
  ) {
    throw new ApiError(0, "INVALID_RESPONSE");
  }
  return base.replace(/\/$/, "");
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  token?: string,
): Promise<T> {
  if (!path.startsWith("/") || path.startsWith("//"))
    throw new ApiError(0, "INVALID_RESPONSE");
  const headers = new Headers(options.headers);
  headers.set("Accept", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);
  let response: Response;
  try {
    response = await fetch(apiBase() + path, {
      ...options,
      headers,
      credentials: "omit",
      cache: "no-store",
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError")
      throw error;
    if (error instanceof ApiError) throw error;
    throw new ApiError(0, "NETWORK_UNAVAILABLE");
  }
  let body: unknown;
  try {
    body = await response.json();
  } catch {
    throw new ApiError(response.status, "INVALID_RESPONSE");
  }
  if (!response.ok) {
    const detail = isObject(body) && isObject(body.error) ? body.error : {};
    throw new ApiError(
      response.status,
      typeof detail.code === "string" ? detail.code : "REQUEST_FAILED",
      typeof detail.request_id === "string" ? detail.request_id : undefined,
    );
  }
  // Stable structures come from generated contracts; security-critical login
  // responses also receive runtime checks before establishing a session.
  return body as T;
}

export async function apiDownload(
  path: string,
  token: string,
  signal?: AbortSignal,
): Promise<{ blob: Blob; filename: string }> {
  if (!path.startsWith("/") || path.startsWith("//"))
    throw new ApiError(0, "INVALID_RESPONSE");
  let response: Response;
  try {
    response = await fetch(apiBase() + path, {
      headers: {
        Accept: "text/csv",
        Authorization: `Bearer ${token}`,
      },
      credentials: "omit",
      cache: "no-store",
      signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError")
      throw error;
    throw new ApiError(0, "NETWORK_UNAVAILABLE");
  }
  if (!response.ok) {
    let body: unknown;
    try {
      body = await response.json();
    } catch {
      throw new ApiError(response.status, "INVALID_RESPONSE");
    }
    const detail = isObject(body) && isObject(body.error) ? body.error : {};
    throw new ApiError(
      response.status,
      typeof detail.code === "string" ? detail.code : "REQUEST_FAILED",
      typeof detail.request_id === "string" ? detail.request_id : undefined,
    );
  }
  const blob = await response.blob();
  const disposition = response.headers.get("Content-Disposition") ?? "";
  const match = /filename="([a-zA-Z0-9._-]+\.csv)"/i.exec(disposition);
  return { blob, filename: match?.[1] ?? "validation-feedback.csv" };
}
