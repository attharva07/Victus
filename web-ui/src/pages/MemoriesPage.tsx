import { FormEvent, useState } from 'react';
import { Card } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { useAuth } from '../lib/authStore';
import { request, requestWithFallback } from '../lib/apiClient';
import { MemoryItem } from '../lib/types';
import { useToast } from '../components/ui/toast';

export const MemoriesPage = () => {
  const { token, apiBaseUrl } = useAuth();
  const { pushToast } = useToast();
  const [query, setQuery] = useState('');
  const [content, setContent] = useState('');
  const [items, setItems] = useState<MemoryItem[]>([]);

  const search = async (event?: FormEvent) => {
    event?.preventDefault();
    try {
      const response = await requestWithFallback<{ items: MemoryItem[] }>(
        apiBaseUrl,
        [`/memory/search?q=${encodeURIComponent(query)}`, `/api/memory/search?query=${encodeURIComponent(query)}`, '/memory'],
        { token },
      );
      setItems(response.items ?? []);
    } catch (error) {
      pushToast(error instanceof Error ? error.message : 'Memory search failed');
    }
  };

  const addMemory = async (event: FormEvent) => {
    event.preventDefault();
    try {
      await request(apiBaseUrl, '/memory', {
        method: 'POST',
        token,
        body: { type: 'note', content, source: 'web-ui', tags: [] },
      });
      setContent('');
      pushToast('Memory added', 'success');
      await search();
    } catch (error) {
      pushToast(error instanceof Error ? error.message : 'Could not add memory');
    }
  };

  const deleteMemory = async (id: string) => {
    if (!window.confirm('Delete this memory?')) return;
    try {
      await request(apiBaseUrl, `/memory/${id}`, { method: 'DELETE', token });
      setItems((prev) => prev.filter((item) => item.id !== id));
      pushToast('Memory deleted', 'success');
    } catch (error) {
      pushToast(error instanceof Error ? error.message : 'Delete failed');
    }
  };

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card>
        <h2 className="mb-3 text-lg font-semibold">Search memories</h2>
        <form onSubmit={search} className="flex gap-2">
          <Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search query" />
          <Button type="submit">Search</Button>
        </form>
        <div className="mt-4 space-y-2">
          {items.length === 0 ? <p className="text-sm text-slate-500">No memories to show.</p> : items.map((item) => (
            <div key={item.id} className="rounded border border-border p-3 text-sm">
              <p className="font-medium">{item.content}</p>
              <p className="text-xs text-slate-500">{item.id}</p>
              <Button className="mt-2 bg-red-600 hover:bg-red-500" onClick={() => deleteMemory(item.id)}>Delete</Button>
            </div>
          ))}
        </div>
      </Card>
      <Card>
        <h2 className="mb-3 text-lg font-semibold">Add memory</h2>
        <form onSubmit={addMemory} className="space-y-3">
          <Input value={content} onChange={(event) => setContent(event.target.value)} required placeholder="Memory content" />
          <Button type="submit">Add</Button>
        </form>
      </Card>
    </div>
  );
};
