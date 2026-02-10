import { useMemo, useState } from 'react';
import { Card } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { useAuth } from '../lib/authStore';
import { requestWithFallback } from '../lib/apiClient';
import { useToast } from '../components/ui/toast';
import { LogEntry } from '../lib/types';

export const LogsPage = () => {
  const { token, apiBaseUrl } = useAuth();
  const { pushToast } = useToast();
  const [entries, setEntries] = useState<LogEntry[]>([]);
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState<LogEntry | null>(null);

  const loadLogs = async () => {
    try {
      const response = await requestWithFallback<{ items?: LogEntry[]; logs?: LogEntry[] }>(apiBaseUrl, ['/logs', '/api/logs'], {
        token,
      });
      setEntries(response.items ?? response.logs ?? []);
    } catch (error) {
      pushToast(error instanceof Error ? error.message : 'Could not load logs');
    }
  };

  const filtered = useMemo(() => {
    const needle = query.toLowerCase();
    return entries.filter((entry) => JSON.stringify(entry).toLowerCase().includes(needle));
  }, [entries, query]);

  return (
    <Card>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Live Logs / Audit Viewer</h2>
        <Button onClick={loadLogs}>Refresh</Button>
      </div>
      <Input placeholder="Search logs" value={query} onChange={(event) => setQuery(event.target.value)} className="mb-3" />
      {filtered.length === 0 ? (
        <p className="text-sm text-slate-500">No log entries.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-border text-slate-500">
                <th className="py-2">Timestamp</th><th>Level</th><th>Event</th><th>Domain/Service</th><th>Request ID</th><th />
              </tr>
            </thead>
            <tbody>
              {filtered.map((entry, index) => (
                <tr key={index} className="border-b border-slate-100">
                  <td className="py-2">{entry.timestamp ?? '-'}</td><td>{entry.level ?? '-'}</td><td>{entry.event ?? '-'}</td>
                  <td>{entry.domain ?? entry.service ?? '-'}</td><td>{entry.request_id ?? '-'}</td>
                  <td><Button className="px-2 py-1 text-xs" onClick={() => setSelected(entry)}>View</Button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {selected && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/30 p-4">
          <Card className="w-full max-w-2xl">
            <div className="mb-2 flex justify-between"><h3 className="font-semibold">Log Detail</h3><Button onClick={() => setSelected(null)}>Close</Button></div>
            <pre className="max-h-[60vh] overflow-auto rounded bg-slate-100 p-3 text-xs">{JSON.stringify(selected, null, 2)}</pre>
          </Card>
        </div>
      )}
    </Card>
  );
};
