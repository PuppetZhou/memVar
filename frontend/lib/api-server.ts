import "server-only";

const SERVER_API_BASE = (
  process.env.MEMVAR_API_INTERNAL_BASE ?? "http://127.0.0.1:8000/api/v1"
).replace(/\/$/, "");

export async function getServerJson<T>(path: string): Promise<T> {
  const response = await fetch(`${SERVER_API_BASE}/${path.replace(/^\/+/, "")}`, {
    cache: "no-store",
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
