import { expect, test, type Page, type Request, type Response } from '@playwright/test';

type NetworkCall = {
  method: string;
  url: string;
  requestHeaders: Record<string, string>;
  status?: number;
  responseBody?: string;
};

const API_PREFIX = '/api/';

function normalizeUrl(rawUrl: string): string {
  try {
    const url = new URL(rawUrl);
    return `${url.origin}${url.pathname}`;
  } catch {
    return rawUrl;
  }
}

async function buildCall(request: Request, response?: Response): Promise<NetworkCall> {
  const method = request.method();
  const url = normalizeUrl(request.url());
  const requestHeaders = request.headers();
  if (!response) {
    return { method, url, requestHeaders };
  }

  let responseBody = '';
  try {
    responseBody = await response.text();
  } catch {
    responseBody = '<unable to read response body>';
  }

  return {
    method,
    url,
    requestHeaders,
    status: response.status(),
    responseBody,
  };
}

function formatFailure(call: NetworkCall): string {
  return [
    'Failing request:',
    `method: ${call.method}`,
    `url: ${call.url}`,
    `status: ${call.status ?? 'no response'}`,
    `response body: ${call.responseBody ?? '<none>'}`,
    `request headers: ${JSON.stringify(call.requestHeaders, null, 2)}`,
  ].join('\n');
}

function pickFailingCall(calls: NetworkCall[], pathFragment: string, method: string): NetworkCall | undefined {
  return calls.find(
    (call) =>
      call.method.toUpperCase() === method.toUpperCase() &&
      call.url.includes(pathFragment) &&
      (call.status === undefined || call.status < 200 || call.status >= 300),
  );
}

async function wireAssertions(page: Page): Promise<void> {
  const calls: NetworkCall[] = [];
  page.on('requestfailed', async (request) => {
    if (!request.url().includes(API_PREFIX)) return;
    calls.push(await buildCall(request));
  });

  page.on('response', async (response) => {
    if (!response.url().includes(API_PREFIX)) return;
    calls.push(await buildCall(response.request(), response));
  });

  await page.goto('/');

  await page.getByRole('button', { name: 'Settings' }).click();
  await page.getByPlaceholder('Admin password').fill(process.env.VICTUS_ADMIN_PASSWORD ?? 'victus');

  const unlockResponse = page.waitForResponse(
    (response) => response.url().includes('/api/admin/unlock') && response.request().method() === 'POST',
  );
  await page.getByRole('button', { name: 'Unlock' }).click();
  await unlockResponse;

  await page.getByRole('button', { name: 'Home' }).click();
  await page.getByPlaceholder('Ask or command Victus...').fill('orchestrate a test response');

  const turnResponse = page.waitForResponse(
    (response) => response.url().includes('/api/turn') && response.request().method() === 'POST',
  );
  await page.getByRole('button', { name: 'Send' }).click();
  await turnResponse;

  const failingUnlock = pickFailingCall(calls, '/api/admin/unlock', 'POST');
  if (failingUnlock) {
    throw new Error(formatFailure(failingUnlock));
  }

  const failingTurn = pickFailingCall(calls, '/api/turn', 'POST');
  if (failingTurn) {
    throw new Error(formatFailure(failingTurn));
  }

  const successfulUnlock = calls.find(
    (call) => call.method === 'POST' && call.url.includes('/api/admin/unlock') && call.status && call.status >= 200 && call.status < 300,
  );
  const successfulTurn = calls.find(
    (call) => call.method === 'POST' && call.url.includes('/api/turn') && call.status && call.status >= 200 && call.status < 300,
  );

  expect(successfulUnlock, 'Expected successful login call to /api/admin/unlock').toBeTruthy();
  expect(successfulTurn, 'Expected successful orchestrate call to /api/turn').toBeTruthy();
}

test('UI login and orchestrate flow is wired to backend APIs', async ({ page }) => {
  await wireAssertions(page);
});
