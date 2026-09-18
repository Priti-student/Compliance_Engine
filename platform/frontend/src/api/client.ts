// Typed API client. Uses relative /api paths (Vite proxies to :8001).

const TOKEN_KEY = "lmpc_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}
export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}
export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export async function api<T>(path: string, options: {
  method?: string;
  headers?: HeadersInit;
  body?: unknown;
} = {}): Promise<T> {
  const headers = new Headers(options.headers || {});
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  let body: BodyInit | null | undefined;
  const raw = options.body;
  if (raw !== undefined) {
    if (typeof raw === "string" || raw instanceof FormData || raw instanceof URLSearchParams) {
      body = raw;
    } else {
      headers.set("Content-Type", "application/json");
      body = JSON.stringify(raw);
    }
  }

  const resp = await fetch(`/api${path}`, { ...options, headers, body });
  if (resp.status === 401) {
    clearToken();
    window.dispatchEvent(new Event("lmpc:unauthorized"));
    throw new ApiError(401, "Session expired - please sign in again");
  }
  if (!resp.ok) {
    let detail = resp.statusText;
    try {
      const data = await resp.json();
      detail = data?.detail || detail;
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(resp.status, typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  if (resp.status === 204) return undefined as T;
  return (await resp.json()) as T;
}

/** Authenticated binary download (Pdf/XLSX/JSON evidence) via blob + object URL. */
export async function downloadFile(path: string, filename: string): Promise<void> {
  const resp = await fetch(`/api${path}`, { headers: { Authorization: `Bearer ${getToken() || ""}` } });
  if (!resp.ok) throw new ApiError(resp.status, "download failed");
  const blob = await resp.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

/** URL for <img> tags - the backend accepts the JWT as ?access_token=. */
export function mediaUrl(path: string): string {
  const token = getToken();
  return `/api${path}${path.includes("?") ? "&" : "?"}access_token=${encodeURIComponent(token || "")}`;
}