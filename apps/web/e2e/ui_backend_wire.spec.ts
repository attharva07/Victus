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

const WIRE_ENDPOINTS = new Set(['/bootstrap/status', '/bootstrap/init', '/login', '/orchestrate']);
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
    throw new Error([
      `No request observed for ${method} ${path}`,
      `Observed tracked calls: ${observed || '<none>'}`,
      ...calls.map((call) => formatCall(call))
    ].join('\n\n'));
  }

  const failed = matches.find((call) => call.status < 200 || call.status >= 300);
  if (failed) {
    throw new Error(`Failing backend request:\n${formatCall(failed)}`);
  }
}

test('UI ↔ backend wire test covers bootstrap status + login + orchestrate', async ({ page }) => {
  const calls: RecordedCall[] = [];
  const failedRequests: FailedRequest[] = [];

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

  await page.evaluate(() => window.localStorage.removeItem('victus_token'));

  if (await page.getByLabel('Bootstrap username').isVisible().catch(() => false)) {
    await page.getByLabel('Bootstrap username').fill(process.env.VITE_TEST_USERNAME ?? 'admin');
    await page.getByLabel('Bootstrap password').fill(process.env.VITE_TEST_PASSWORD ?? 'admin123456789');
    await page.getByRole('button', { name: 'Init' }).click();
  }

  await page.getByLabel('Login username').fill(process.env.VITE_TEST_USERNAME ?? 'admin');
  await page.getByLabel('Login password').fill(process.env.VITE_TEST_PASSWORD ?? 'admin123456789');
  await page.getByRole('button', { name: 'Login' }).click();

  await expect(page.getByLabel('Command dock')).toBeVisible();
  await page.getByLabel('Command dock').fill('list recent memories');
  await page.getByLabel('Command dock').press('Enter');

  if (failedRequests.length > 0) {
    throw new Error(`Failing backend request:\n${formatFailedRequest(failedRequests[0])}`);
  }

  assertSuccessfulRequest(calls, '/bootstrap/status', 'GET');
  assertSuccessfulRequest(calls, '/login', 'POST');
  assertSuccessfulRequest(calls, '/orchestrate', 'POST');
});
