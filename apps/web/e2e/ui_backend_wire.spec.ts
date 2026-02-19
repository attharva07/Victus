import { expect, test } from '@playwright/test';

type RecordedCall = {
  method: string;
  url: string;
  path: string;
  status: number;
  requestHeaders: Record<string, string>;
  responseHeaders: Record<string, string>;
  responseBodyExcerpt: string;
};

type FailedRequest = {
  method: string;
  url: string;
  path: string;
  failureText: string | null;
  requestHeaders: Record<string, string>;
};

type JsonFetchResult<T> = {
  status: number;
  data: T;
};

const WIRE_ENDPOINTS = new Set(['/bootstrap/status', '/login', '/orchestrate']);
const DEFAULT_USERNAME = 'admin';
const DEFAULT_PASSWORD = 'admin123';
const MAX_BODY_EXCERPT_CHARS = 500;

function toPathname(rawUrl: string): string {
  try {
    return new URL(rawUrl).pathname;
  } catch {
    return '<invalid-url>';
  }
}

function shorten(text: string, maxChars = MAX_BODY_EXCERPT_CHARS): string {
  return text.length <= maxChars ? text : `${text.slice(0, maxChars)}...(truncated)`;
}

function formatCall(call: RecordedCall): string {
  return [
    `method=${call.method}`,
    `url=${call.url}`,
    `path=${call.path}`,
    `status=${call.status}`,
    `requestHeaders=${JSON.stringify(call.requestHeaders)}`,
    `responseHeaders=${JSON.stringify(call.responseHeaders)}`,
    `responseBodyExcerpt=${call.responseBodyExcerpt}`
  ].join('\n');
}

function formatFailedRequest(call: FailedRequest): string {
  return [
    `method=${call.method}`,
    `url=${call.url}`,
    `path=${call.path}`,
    'status=NETWORK_FAILURE',
    `requestHeaders=${JSON.stringify(call.requestHeaders)}`,
    `responseBody=${call.failureText ?? ''}`
  ].join('\n');
}

function matchingCalls(calls: RecordedCall[], path: string, method: string): RecordedCall[] {
  return calls.filter((call) => call.path === path && call.method === method);
}

function assertSuccessfulRequest(calls: RecordedCall[], path: string, method: string): void {
  const matches = matchingCalls(calls, path, method);
  if (matches.length === 0) {
    const observed = calls.map((call) => `${call.method} ${call.path} (${call.status})`).join(', ');
    throw new Error(
      [`No request observed for ${method} ${path}`, `Observed tracked calls: ${observed || '<none>'}`].join('\n')
    );
  }

  const failed = matches.find((call) => call.status < 200 || call.status >= 300);
  if (failed) {
    throw new Error(`Failing backend request:\n${formatCall(failed)}`);
  }
}

test('UI ↔ backend wire test covers bootstrap status + login + orchestrate', async ({ page }) => {
  const calls: RecordedCall[] = [];
  const failedRequests: FailedRequest[] = [];

  const username = process.env.VICTUS_TEST_USERNAME ?? DEFAULT_USERNAME;
  const password = process.env.VICTUS_TEST_PASSWORD ?? DEFAULT_PASSWORD;
  const apiBase = (process.env.VICTUS_TEST_API_BASE ?? '').trim().replace(/\/$/, '');

  page.on('response', async (response) => {
    const request = response.request();
    const url = response.url();
    const path = toPathname(url);
    if (!WIRE_ENDPOINTS.has(path)) {
      return;
    }

    let responseBodyExcerpt = '<unavailable>';
    try {
      responseBodyExcerpt = shorten(await response.text());
    } catch {
      // Ignore body read failures and keep diagnostics marker.
    }

    calls.push({
      method: request.method(),
      url,
      path,
      status: response.status(),
      requestHeaders: await request.allHeaders(),
      responseHeaders: await response.allHeaders(),
      responseBodyExcerpt
    });
  });

  page.on('requestfailed', async (request) => {
    const url = request.url();
    const path = toPathname(url);
    if (!WIRE_ENDPOINTS.has(path)) {
      return;
    }

    failedRequests.push({
      method: request.method(),
      url,
      path,
      failureText: request.failure()?.errorText ?? null,
      requestHeaders: await request.allHeaders()
    });
  });

  await page.goto('/');

  const accessToken = await page.evaluate(
    async ({ inUsername, inPassword, inApiBase }) => {
      const endpoint = (path: string): string => (inApiBase ? `${inApiBase}${path}` : path);

      const fetchJsonWithDiagnostics = async <T>(path: string, init?: RequestInit): Promise<JsonFetchResult<T>> => {
        const requestUrl = endpoint(path);
        const response = await fetch(requestUrl, init);
        const contentType = response.headers.get('content-type') ?? '';
        const bodyText = await response.text();

        if (!contentType.toLowerCase().includes('application/json')) {
          const htmlLike = bodyText.trim().startsWith('<');
          const details = [
            `Expected JSON response for ${path}`,
            `requestUrl=${requestUrl}`,
            `status=${response.status}`,
            `content-type=${contentType || '<missing>'}`,
            `bodyExcerpt=${bodyText.slice(0, 300)}`
          ];
          if (htmlLike) {
            details.push('htmlDetected=true');
          }
          throw new Error(details.join('\n'));
        }

        let parsed: T;
        try {
          parsed = JSON.parse(bodyText) as T;
        } catch {
          throw new Error(
            [
              `Invalid JSON response for ${path}`,
              `requestUrl=${requestUrl}`,
              `status=${response.status}`,
              `content-type=${contentType || '<missing>'}`,
              `bodyExcerpt=${bodyText.slice(0, 300)}`
            ].join('\n')
          );
        }

        if (!response.ok) {
          throw new Error(
            [
              `Non-success JSON response for ${path}`,
              `requestUrl=${requestUrl}`,
              `status=${response.status}`,
              `content-type=${contentType || '<missing>'}`,
              `bodyExcerpt=${bodyText.slice(0, 300)}`
            ].join('\n')
          );
        }

        return { status: response.status, data: parsed };
      };

      const statusResult = await fetchJsonWithDiagnostics<{ bootstrapped: boolean }>('/bootstrap/status');
      if (!statusResult.data.bootstrapped) {
        throw new Error('Expected backend to be bootstrapped before wire test execution');
      }

      const loginResult = await fetchJsonWithDiagnostics<{ access_token: string }>('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: inUsername, password: inPassword })
      });

      if (!loginResult.data.access_token) {
        throw new Error('login response missing access_token');
      }

      return loginResult.data.access_token;
    },
    { inUsername: username, inPassword: password, inApiBase: apiBase }
  );

  await expect(page.getByLabel('Command dock')).toBeVisible();

  const orchestrateResult = await page.evaluate(
    async ({ token, inApiBase }) => {
      const requestUrl = inApiBase ? `${inApiBase}/orchestrate` : '/orchestrate';
      const response = await fetch(requestUrl, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text: 'list recent memories' })
      });

      const contentType = response.headers.get('content-type') ?? '';
      const bodyText = await response.text();
      if (!response.ok) {
        throw new Error(
          [
            'orchestrate request failed',
            `requestUrl=${requestUrl}`,
            `status=${response.status}`,
            `content-type=${contentType || '<missing>'}`,
            `bodyExcerpt=${bodyText.slice(0, 300)}`
          ].join('\n')
        );
      }

      return {
        status: response.status,
        contentType,
        bodyExcerpt: bodyText.slice(0, 300)
      };
    },
    { token: accessToken, inApiBase: apiBase }
  );

  expect(orchestrateResult.status).toBeGreaterThanOrEqual(200);
  expect(orchestrateResult.status).toBeLessThan(300);

  if (failedRequests.length > 0) {
    throw new Error(`Failing backend request:\n${formatFailedRequest(failedRequests[0])}`);
  }

  assertSuccessfulRequest(calls, '/bootstrap/status', 'GET');
  assertSuccessfulRequest(calls, '/login', 'POST');
  assertSuccessfulRequest(calls, '/orchestrate', 'POST');
});
