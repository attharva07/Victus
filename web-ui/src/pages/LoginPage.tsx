import { FormEvent, useState } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import { Card } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { useAuth } from '../lib/authStore';
import { request } from '../lib/apiClient';
import { useToast } from '../components/ui/toast';

export const LoginPage = () => {
  const [tokenInput, setTokenInput] = useState('');
  const [loading, setLoading] = useState(false);
  const { token, setToken, apiBaseUrl } = useAuth();
  const navigate = useNavigate();
  const { pushToast } = useToast();

  if (token) return <Navigate to="/app/chat" replace />;

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    try {
      await request(apiBaseUrl, '/me', { token: tokenInput.trim() });
      setToken(tokenInput.trim());
      navigate('/app/chat');
      pushToast('Login verified via /me.', 'success');
    } catch (error) {
      pushToast(error instanceof Error ? error.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <Card className="w-full max-w-md">
        <h1 className="mb-1 text-xl font-semibold">Victus Login</h1>
        <p className="mb-4 text-sm text-slate-500">Token is stored in memory only for this tab session.</p>
        <form onSubmit={onSubmit} className="space-y-3">
          <Input
            type="password"
            required
            placeholder="Paste API token"
            value={tokenInput}
            onChange={(event) => setTokenInput(event.target.value)}
          />
          <Button type="submit" disabled={loading} className="w-full">
            {loading ? 'Verifying…' : 'Login'}
          </Button>
        </form>
      </Card>
    </div>
  );
};
