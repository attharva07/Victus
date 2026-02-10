import { FormEvent, useState } from 'react';
import { Card } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { useAuth } from '../lib/authStore';
import { request, requestWithFallback } from '../lib/apiClient';
import { Transaction } from '../lib/types';
import { useToast } from '../components/ui/toast';

export const FinancePage = () => {
  const { token, apiBaseUrl } = useAuth();
  const { pushToast } = useToast();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [summary, setSummary] = useState<Record<string, unknown> | null>(null);
  const [amount, setAmount] = useState('');
  const [category, setCategory] = useState('general');

  const load = async () => {
    try {
      const tx = await requestWithFallback<{ items?: Transaction[]; transactions?: Transaction[] }>(apiBaseUrl, ['/finance/transactions', '/api/finance/transactions'], { token });
      const sm = await requestWithFallback<Record<string, unknown>>(apiBaseUrl, ['/finance/summary', '/api/finance/summary'], { token });
      setTransactions(tx.items ?? tx.transactions ?? []);
      setSummary(sm);
    } catch (error) {
      pushToast(error instanceof Error ? error.message : 'Could not load finance data');
    }
  };

  const add = async (event: FormEvent) => {
    event.preventDefault();
    try {
      await requestWithFallback(apiBaseUrl, ['/finance/transaction', '/api/finance/transaction'], {
        method: 'POST',
        token,
        body: { amount: Number(amount), category },
      });
      setAmount('');
      pushToast('Transaction added', 'success');
      await load();
    } catch (error) {
      pushToast(error instanceof Error ? error.message : 'Transaction failed');
    }
  };

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card>
        <div className="mb-3 flex items-center justify-between"><h2 className="text-lg font-semibold">Transactions</h2><Button onClick={load}>Refresh</Button></div>
        {transactions.length === 0 ? <p className="text-sm text-slate-500">No transactions.</p> : (
          <div className="space-y-2 text-sm">{transactions.map((tx, i) => <div key={i} className="rounded border p-2">{tx.category}: {tx.amount}</div>)}</div>
        )}
      </Card>
      <Card>
        <h2 className="mb-3 text-lg font-semibold">Add transaction</h2>
        <form onSubmit={add} className="space-y-2">
          <Input type="number" value={amount} onChange={(event) => setAmount(event.target.value)} required placeholder="Amount" />
          <Input value={category} onChange={(event) => setCategory(event.target.value)} required placeholder="Category" />
          <Button type="submit">Submit</Button>
        </form>
        <h3 className="mt-6 font-semibold">Summary</h3>
        <pre className="rounded bg-slate-100 p-3 text-xs">{summary ? JSON.stringify(summary, null, 2) : 'No summary loaded.'}</pre>
      </Card>
    </div>
  );
};
