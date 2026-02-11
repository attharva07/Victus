import { useState } from 'react';
import { Card } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { useAuth } from '../lib/authStore';
import { requestWithFallback } from '../lib/apiClient';
import { useToast } from '../components/ui/toast';

export const FilesPage = () => {
  const { token, apiBaseUrl } = useAuth();
  const { pushToast } = useToast();
  const [path, setPath] = useState('.');
  const [listData, setListData] = useState<unknown>(null);
  const [fileContent, setFileContent] = useState('');

  const listFiles = async () => {
    try {
      const result = await requestWithFallback<Record<string, unknown>>(apiBaseUrl, [`/files/list?path=${encodeURIComponent(path)}`, `/api/files/list?path=${encodeURIComponent(path)}`], { token });
      setListData(result);
    } catch (error) {
      pushToast(error instanceof Error ? error.message : 'List files failed');
    }
  };

  const readFile = async () => {
    try {
      const result = await requestWithFallback<Record<string, unknown>>(apiBaseUrl, [`/files/read?path=${encodeURIComponent(path)}`, `/api/files/read?path=${encodeURIComponent(path)}`], { token });
      setFileContent(String(result.content ?? JSON.stringify(result, null, 2)));
    } catch (error) {
      pushToast(error instanceof Error ? error.message : 'Read file failed');
    }
  };

  return (
    <Card>
      <h2 className="mb-3 text-lg font-semibold">Files</h2>
      <div className="mb-3 flex gap-2"><Input value={path} onChange={(event) => setPath(event.target.value)} /><Button onClick={listFiles}>List</Button><Button onClick={readFile}>Read</Button></div>
      <pre className="mb-3 rounded bg-slate-100 p-3 text-xs">{listData ? JSON.stringify(listData, null, 2) : 'No listing loaded.'}</pre>
      <pre className="rounded bg-slate-100 p-3 text-xs">{fileContent || 'No file selected.'}</pre>
    </Card>
  );
};
