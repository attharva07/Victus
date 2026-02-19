import { expect, test } from '@playwright/test';

type RecordedCall = {
  method: string;
  url: string;
  status: number;
  responseBody: string;
  requestHeaders: Record<string, string>;
};

type FailedRequest = {
  method: string;
  url: string;
  failureText: string | null;
  requestHeaders: Record<string, string>;
};

function formatCall(call: RecordedCall): string {
  return [
    `method=${call.method}`,
    `url=${call.url}`,
    `status=${call.status}`,
    `requestHeaders=${JSON.stringify(call.requestHeaders)}`,
    `responseBody=${call.responseBody}`
  ].join('\n');
}

function formatFailedRequest(call: FailedRequest): string {
  return [
    `method=${call.method}`,
    `url=${call.url}`,
    `status=NETWORK_FAILURE`,
    `requestHeaders=${JSON.stringify(call.requestHeaders)}`,
    `responseBody=${call.failureText ?? ''}`
  ].join('\n');
}

function matchingCalls(calls: RecordedCall[], path: string, method: string): RecordedCall[] {
  return calls.filter((call) => new URL(call.url).pathname === path && call.method === method);
}

function assertSuccessfulRequest(calls: RecordedCall[], path: string, method: string): void {
  const matches = matchingCalls(calls, path, method);
  if (matches.length === 0) {
    throw new Error(`No request observed for ${method} ${path}`);
  }
  const failed = matches.find((call) => call.status < 200 || call.status >= 300);
  if (failed) {
    throw new Error(`Failing backend request:\n${formatCall(failed)}`);
  }
}


test('UI ↔ backend wire test covers login + orchestrate network calls', async ({ page }) => {
  const calls: RecordedCall[] = [];
  const failedRequests: FailedRequest[] = [];

  page.on('response', async (response) => {
    const request = response.request();
    const url = response.url();
    if (!url.startsWith('http://127.0.0.1:8000')) {
      return;
    }
    let responseBody = '';
    try {
      responseBody = await response.text();
    } catch {
      responseBody = '<unavailable>';
    }
    calls.push({
      method: request.method(),
      url,
      status: response.status(),
      responseBody,
      requestHeaders: await request.allHeaders()
    });
  });

  page.on('requestfailed', async (request) => {
    const url = request.url();
    if (!url.startsWith('http://127.0.0.1:8000')) {
      return;
    }
    failedRequests.push({
      method: request.method(),
      url,
      failureText: request.failure()?.errorText ?? null,
      requestHeaders: await request.allHeaders()
    });
  });

  await page.goto('/');

  const token = await page.evaluate(async () => {
    const fetchJsonWithDiagnostics = async (path: string, init?: RequestInit) => {
      const response = await fetch(path, init);
      const contentType = response.headers.get('content-type') ?? '';
      if (!contentType.toLowerCase().includes('application/json')) {
        const body = await response.text();
        throw new Error(
          [
            `Expected JSON response for ${path}`,
            `status=${response.status}`,
            `content-type=${contentType || '<missing>'}`,
            `body=${body}`
          ].join('\n')
        );
      }

      const body = await response.json();
      return { response, body };
    };

    const { body: statusData } = (await fetchJsonWithDiagnostics('/bootstrap/status')) as {
      body: { bootstrapped: boolean };
    };
    const username = 'admin';
    const password = 'WireTestPassword123!';

    if (!statusData.bootstrapped) {
      const bootstrapResponse = await fetch('/bootstrap/init', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      if (!bootstrapResponse.ok && bootstrapResponse.status !== 409) {
        throw new Error(`bootstrap/init failed with status ${bootstrapResponse.status}`);
      }
    }

    const { response: loginResponse, body: loginData } = (await fetchJsonWithDiagnostics('/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    })) as { response: Response; body: { access_token: string } };
    if (!loginResponse.ok) {
      throw new Error(`login failed with status ${loginResponse.status}`);
    }
    return loginData.access_token;
  });

  await expect(page.getByLabel('Command dock')).toBeVisible();
  await page.getByLabel('Command dock').fill('run wire check');
  await page.getByLabel('Command dock').press('Enter');

  const orchestrateResponse = await page.evaluate(async ({ accessToken }) => {
    const response = await fetch('/orchestrate', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ text: 'list recent memories' })
    });
    const body = await response.text();
    return { status: response.status, body };
  }, { accessToken: token });

  expect(orchestrateResponse.status).toBeGreaterThanOrEqual(200);
  expect(orchestrateResponse.status).toBeLessThan(300);

  if (failedRequests.length > 0) {
    throw new Error(`Failing backend request:\n${formatFailedRequest(failedRequests[0])}`);
  }

  assertSuccessfulRequest(calls, '/login', 'POST');
  assertSuccessfulRequest(calls, '/orchestrate', 'POST');
});
