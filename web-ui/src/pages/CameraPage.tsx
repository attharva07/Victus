import { useState } from 'react';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { useAuth } from '../lib/authStore';
import { requestWithFallback } from '../lib/apiClient';
import { useToast } from '../components/ui/toast';

export const CameraPage = () => {
  const { token, apiBaseUrl } = useAuth();
  const { pushToast } = useToast();
  const [status, setStatus] = useState<unknown>(null);
  const [captureResult, setCaptureResult] = useState<unknown>(null);

  const loadStatus = async () => {
    try {
      setStatus(await requestWithFallback(apiBaseUrl, ['/camera/status', '/api/camera/status'], { token }));
    } catch (error) {
      pushToast(error instanceof Error ? error.message : 'Status failed');
    }
  };

  const capture = async () => {
    try {
      setCaptureResult(await requestWithFallback(apiBaseUrl, ['/camera/capture', '/api/camera/capture'], { method: 'POST', token }));
    } catch (error) {
      pushToast(error instanceof Error ? error.message : 'Capture failed');
    }
  };

  return (
    <Card>
      <h2 className="mb-3 text-lg font-semibold">Camera</h2>
      <div className="mb-3 flex gap-2"><Button onClick={loadStatus}>Get status</Button><Button onClick={capture}>Capture</Button></div>
      <pre className="mb-3 rounded bg-slate-100 p-3 text-xs">{status ? JSON.stringify(status, null, 2) : 'No camera status.'}</pre>
      <pre className="rounded bg-slate-100 p-3 text-xs">{captureResult ? JSON.stringify(captureResult, null, 2) : 'No capture result.'}</pre>
    </Card>
  );
};
