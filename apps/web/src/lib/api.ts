const TOKEN_STORAGE_KEY = 'victus_token';
const MAX_ERROR_EXCERPT_CHARS = 400;
const API_BASE_URL = (import.meta.env.VITE_API_URL ?? '').trim();

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

function isJsonContentType(contentType: string | null): boolean {
  return Boolean(contentType && contentType.toLowerCase().includes('application/json'));
}

function hasHttpProtocol(path: string): boolean {
  return /^https?:\/\//i.test(path);
}

function buildRequestUrl(path: string): string {
  if (!API_BASE_URL || hasHttpProtocol(path)) {
    return path;
  }

  const normalizedBase = API_BASE_URL.endsWith('/') ? API_BASE_URL.slice(0, -1) : API_BASE_URL;
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${normalizedBase}${normalizedPath}`;
}

export async function parseApiBody<T = unknown>(response: Response): Promise<T> {
  const text = await response.text();
  if (!text.trim()) {
    return '' as T;
  }

  if (isJsonContentType(response.headers.get('content-type'))) {
    return JSON.parse(text) as T;
  }

  return text as T;
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

export async function apiFetch<T = unknown>(path: string, opts: RequestInit = {}): Promise<T> {
  const headers = new Headers(opts.headers ?? {});
  const method = (opts.method ?? 'GET').toUpperCase();
  const requestUrl = buildRequestUrl(path);

  if (opts.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const token = getToken();
  if (path !== '/login' && token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const response = await fetch(requestUrl, { ...opts, headers });

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

  return parseApiBody<T>(response);
}

export async function login(username: string, password: string): Promise<string> {
  const data = await apiFetch<{ access_token?: string }>('/login', {
    method: 'POST',
    body: JSON.stringify({ username, password })
  });

  const token = data.access_token?.trim();
  if (!token) {
    throw new ApiError({
      message: 'POST /login succeeded but response did not include access_token.',
      status: 200,
      contentType: 'application/json',
      bodyExcerpt: '<missing access_token>',
      path: '/login',
      method: 'POST'
    });
  }

  setToken(token);
  return token;
}

export async function bootstrapStatus(): Promise<{ bootstrapped: boolean }> {
  return apiFetch<{ bootstrapped: boolean }>('/bootstrap/status');
}

export async function bootstrapInit(username: string, password: string): Promise<{ ok: boolean; bootstrapped: boolean }> {
  return apiFetch<{ ok: boolean; bootstrapped: boolean }>('/bootstrap/init', {
    method: 'POST',
    body: JSON.stringify({ username, password })
  });
}

const useMocks = import.meta.env.VITE_USE_MOCKS === 'true';

export async function orchestrate(text: string): Promise<unknown> {
  if (useMocks) {
    return {
      ok: true,
      mode: 'local',
      message: 'Acknowledged. Command received in local mode.',
      text
    };
  }

  return apiFetch<unknown>('/orchestrate', {
    method: 'POST',
    body: JSON.stringify({ text })
  });
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
  return apiFetch<{ results: unknown[] }>(`/memory/search?q=${encodeURIComponent(q)}&limit=${limit}`);
}

export async function memoriesList(limit = 20): Promise<{ results: unknown[] }> {
  return apiFetch<{ results: unknown[] }>(`/memory/list?limit=${limit}`);
}

export async function financeSummary(period = 'week'): Promise<{ report: unknown }> {
  return apiFetch<{ report: unknown }>(`/finance/summary?period=${encodeURIComponent(period)}`);
}

export async function filesList(): Promise<{ files: string[] }> {
  return apiFetch<{ files: string[] }>('/files/list');
}

export async function cameraStatus(): Promise<unknown> {
  return apiFetch<unknown>('/camera/status');
}
