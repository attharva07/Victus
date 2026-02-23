const TOKEN_STORAGE_KEY = 'victus_token';

let tokenCache: string | null = null;

export function getApiBase(): string {
  const configured = (import.meta.env.VITE_API_URL ?? '').trim();
  return configured.replace(/\/$/, '');
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

  if (opts.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const token = getToken();
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  return fetch(url, { ...opts, headers });
}
