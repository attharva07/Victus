import { FormEvent, useState } from 'react';
import { Card } from '../components/ui/card';
import { Textarea } from '../components/ui/textarea';
import { Button } from '../components/ui/button';
import { requestWithFallback } from '../lib/apiClient';
import { useAuth } from '../lib/authStore';
import { useToast } from '../components/ui/toast';

type ChatMessage = { role: 'user' | 'assistant'; content: string };

export const ChatPage = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const { token, apiBaseUrl } = useAuth();
  const { pushToast } = useToast();

  const onSend = async (event: FormEvent) => {
    event.preventDefault();
    if (!text.trim()) return;
    const input = text.trim();
    setMessages((prev) => [...prev, { role: 'user', content: input }]);
    setText('');
    setLoading(true);
    try {
      const response = await requestWithFallback<Record<string, unknown>>(apiBaseUrl, ['/chat', '/api/chat'], {
        method: 'POST',
        token,
        body: { message: input },
      });
      const output = String(response.response ?? response.message ?? JSON.stringify(response));
      setMessages((prev) => [...prev, { role: 'assistant', content: output }]);
    } catch (error) {
      pushToast(error instanceof Error ? error.message : 'Chat failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <h2 className="mb-4 text-lg font-semibold">Chat / Orchestrate</h2>
      <div className="mb-4 space-y-3">
        {messages.length === 0 && <p className="text-sm text-slate-500">No messages yet.</p>}
        {messages.map((message, index) => (
          <div key={`${message.role}-${index}`} className={`rounded-lg p-3 text-sm ${message.role === 'user' ? 'bg-slate-100' : 'bg-emerald-50'}`}>
            <strong className="mr-2 capitalize">{message.role}:</strong>
            {message.content}
          </div>
        ))}
      </div>
      <form onSubmit={onSend} className="space-y-3">
        <Textarea value={text} onChange={(event) => setText(event.target.value)} rows={4} placeholder="Send a message" />
        <Button type="submit" disabled={loading}>{loading ? 'Sending…' : 'Send'}</Button>
      </form>
    </Card>
  );
};
