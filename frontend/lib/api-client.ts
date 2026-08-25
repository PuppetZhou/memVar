const SAME_ORIGIN_API_BASE = "/api/v1";

function apiPath(path: string): string {
  return `${SAME_ORIGIN_API_BASE}/${path.replace(/^\/+/, "")}`;
}

export async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(apiPath(path), {
    signal,
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch { /* Use the HTTP status when no JSON error body is available. */ }
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

export function resolveApiUrl(path: string): string {
  if (/^https?:\/\//i.test(path)) {
    const url = new URL(path);
    return url.pathname.startsWith(`${SAME_ORIGIN_API_BASE}/`)
      ? `${url.pathname}${url.search}${url.hash}`
      : path;
  }
  if (path.startsWith("/api/")) return path;
  return apiPath(path);
}
