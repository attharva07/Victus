import { useState } from 'react';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { useAuth } from '../lib/authStore';
import { ApiError, requestWithFallback } from '../lib/apiClient';
import { useToast } from '../components/ui/toast';

export const SettingsPage = () => {
  const { token, apiBaseUrl } = useAuth();
  const { pushToast } = useToast();
  const [settings, setSettings] = useState<Record<string, boolean>>({});
  const [readOnly, setReadOnly] = useState(false);

  const load = async () => {
    try {
      const result = await requestWithFallback<Record<string, boolean>>(apiBaseUrl, ['/settings', '/api/settings'], { token });
      setSettings(result);
      setReadOnly(false);
    } catch (error) {
      pushToast(error instanceof Error ? error.message : 'Could not load settings');
    }
  };

  const save = async () => {
    try {
      await requestWithFallback(apiBaseUrl, ['/settings', '/api/settings'], { method: 'PATCH', token, body: settings });
      pushToast('Settings updated', 'success');
    } catch (error) {
      if (error instanceof ApiError && (error.status === 404 || error.status === 405)) {
        setReadOnly(true);
        pushToast('Settings endpoint is read-only on this backend.');
        return;
      }
      pushToast(error instanceof Error ? error.message : 'Could not save settings');
    }
  };

  return (
    <Card>
      <div className="mb-3 flex items-center justify-between"><h2 className="text-lg font-semibold">Settings</h2><Button onClick={load}>Refresh</Button></div>
      {Object.keys(settings).length === 0 ? <p className="text-sm text-slate-500">No settings loaded.</p> : (
        <div className="space-y-2">{Object.entries(settings).map(([key, value]) => (
          <label key={key} className="flex items-center justify-between rounded border p-3 text-sm">
            <span>{key}</span>
            <input type="checkbox" checked={value} disabled={readOnly} onChange={(event) => setSettings((prev) => ({ ...prev, [key]: event.target.checked }))} />
          </label>
        ))}</div>
      )}
      <Button onClick={save} className="mt-3" disabled={readOnly}>Save</Button>
      {readOnly && <p className="mt-2 text-xs text-slate-500">Write endpoint unavailable; viewing settings in read-only mode.</p>}
    </Card>
  );
};
