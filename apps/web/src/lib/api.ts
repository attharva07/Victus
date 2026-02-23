const TOKEN_STORAGE_KEY = 'victus_token';
const MAX_ERROR_EXCERPT_CHARS = 400;

let tokenCache: string | null = null;

export type ApiErrorDetails = {
  message: string;
  status: number;
  contentType: string | null;
  bodyExcerpt: string;
  path: string;
  method: string;
};

export class ApiError extends Error {
  status: number;
  contentType: string | null;
  bodyExcerpt: string;
  path: string;
  method: string;

  constructor(details: ApiErrorDetails) {
    super(details.message);
    this.name = 'ApiError';
    this.status = details.status;
    this.contentType = details.contentType;
    this.bodyExcerpt = details.bodyExcerpt;
    this.path = details.path;
    this.method = details.method;
  }
}

function shorten(text: string): string {
  return text.length > MAX_ERROR_EXCERPT_CHARS ? `${text.slice(0, MAX_ERROR_EXCERPT_CHARS)}...(truncated)` : text;
}

async function parseJsonResponse<T>(response: Response): Promise<T> {
  const text = await response.text();
  if (!text.trim()) {
    return {} as T;
  }
  return JSON.parse(text) as T;
}

export function getApiBase(): string {
  const configured = (import.meta.env.VITE_API_URL ?? '').trim();
  return configured ? configured.replace(/\/$/, '') : '';
}

export function getToken(): string | null {
  if (tokenCache) {
    return tokenCache;
  }

  if (typeof window === 'undefined') {
    return null;
  }

  const stored = window.localStorage.getItem(TOKEN_STORAGE_KEY);
  tokenCache = stored;
  return stored;
}

export function setToken(token: string | null): void {
  tokenCache = token;
  if (typeof window === 'undefined') {
    return;
  }

  if (token) {
    window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
    return;
  }

  window.localStorage.removeItem(TOKEN_STORAGE_KEY);
}

export async function apiFetch(path: string, opts: RequestInit = {}): Promise<Response> {
  const base = getApiBase();
  const url = `${base}${path}`;
  const headers = new Headers(opts.headers ?? {});
  const method = (opts.method ?? 'GET').toUpperCase();

  if (opts.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const token = getToken();
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const response = await fetch(url, { ...opts, headers });

  if (!response.ok) {
    const contentType = response.headers.get('content-type');
    let bodyExcerpt = '<unavailable>';
    try {
      bodyExcerpt = shorten(await response.text());
    } catch {
      bodyExcerpt = '<failed to read response body>';
    }

    throw new ApiError({
      message: `${method} ${path} failed with status ${response.status}`,
      status: response.status,
      contentType,
      bodyExcerpt,
      path,
      method
    });
  }

  return response;
}

export async function login(username: string, password: string): Promise<string> {
  const response = await apiFetch('/login', {
    method: 'POST',
    body: JSON.stringify({ username, password })
  });
  const data = await parseJsonResponse<{ access_token?: string }>(response);
  const token = data.access_token?.trim();
  if (!token) {
    throw new ApiError({
      message: 'POST /login succeeded but response did not include access_token.',
      status: response.status,
      contentType: response.headers.get('content-type'),
      bodyExcerpt: '<missing access_token>',
      path: '/login',
      method: 'POST'
    });
  }
  setToken(token);
  return token;
}

export async function bootstrapStatus(): Promise<{ bootstrapped: boolean }> {
  const response = await apiFetch('/bootstrap/status');
  return parseJsonResponse<{ bootstrapped: boolean }>(response);
}

export async function bootstrapInit(username: string, password: string): Promise<{ ok: boolean; bootstrapped: boolean }> {
  const response = await apiFetch('/bootstrap/init', {
    method: 'POST',
    body: JSON.stringify({ username, password })
  });
  return parseJsonResponse<{ ok: boolean; bootstrapped: boolean }>(response);
}

export async function orchestrate(text: string): Promise<unknown> {
  const response = await apiFetch('/orchestrate', {
    method: 'POST',
    body: JSON.stringify({ text })
  });
  return parseJsonResponse<unknown>(response);
}

export async function validateStoredToken(): Promise<boolean> {
  if (!getToken()) {
    return false;
  }

  try {
    await apiFetch('/me');
    return true;
  } catch (error) {
    if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
      setToken(null);
      return false;
    }
    throw error;
  }
}

export async function memoriesSearch(q: string, limit = 20): Promise<{ results: unknown[] }> {
  const response = await apiFetch(`/memory/search?q=${encodeURIComponent(q)}&limit=${limit}`);
  return parseJsonResponse<{ results: unknown[] }>(response);
}

export async function memoriesList(limit = 20): Promise<{ results: unknown[] }> {
  const response = await apiFetch(`/memory/list?limit=${limit}`);
  return parseJsonResponse<{ results: unknown[] }>(response);
}

export async function financeSummary(period = 'week'): Promise<{ report: unknown }> {
  const response = await apiFetch(`/finance/summary?period=${encodeURIComponent(period)}`);
  return parseJsonResponse<{ report: unknown }>(response);
}

export async function filesList(): Promise<{ files: string[] }> {
  const response = await apiFetch('/files/list');
  return parseJsonResponse<{ files: string[] }>(response);
}

export async function cameraStatus(): Promise<unknown> {
  const response = await apiFetch('/camera/status');
  return parseJsonResponse<unknown>(response);
}
