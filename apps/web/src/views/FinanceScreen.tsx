import { FormEvent, useMemo, useState } from 'react';

type Transaction = {
  id: string;
  label: string;
  amount: number;
  type: 'income' | 'expense';
};

const initialTransactions: Transaction[] = [
  { id: 'tx-1', label: 'Cloud spend', amount: 280, type: 'expense' },
  { id: 'tx-2', label: 'Consulting invoice', amount: 900, type: 'income' },
  { id: 'tx-3', label: 'Tooling licenses', amount: 120, type: 'expense' }
];

export default function FinanceScreen() {
  const [transactions, setTransactions] = useState(initialTransactions);
  const [label, setLabel] = useState('');
  const [amount, setAmount] = useState('');
  const [type, setType] = useState<Transaction['type']>('expense');

  const totals = useMemo(() => {
    const income = transactions.filter((tx) => tx.type === 'income').reduce((sum, tx) => sum + tx.amount, 0);
    const expense = transactions.filter((tx) => tx.type === 'expense').reduce((sum, tx) => sum + tx.amount, 0);
    return { income, expense, net: income - expense };
  }, [transactions]);

  const addTransaction = (event: FormEvent) => {
    event.preventDefault();
    const parsedAmount = Number(amount);
    if (!label.trim() || Number.isNaN(parsedAmount) || parsedAmount <= 0) return;

    setTransactions((prev) => [{ id: `tx-${Date.now()}`, label: label.trim(), amount: parsedAmount, type }, ...prev]);
    setLabel('');
    setAmount('');
    setType('expense');
  };

  return (
    <section className="grid h-full grid-cols-[minmax(0,1fr)_300px] gap-3 rounded-xl border border-borderSoft/80 bg-panel/60 p-3">
      <div className="min-h-0 rounded-lg border border-borderSoft/70 bg-panel px-3 py-2">
        <header className="mb-3 flex items-baseline justify-between">
          <h2 className="text-sm uppercase tracking-[0.14em] text-slate-300">Transactions</h2>
          <p className="text-xs text-slate-500">{transactions.length} entries</p>
        </header>
        <ul className="h-[calc(100%-2rem)] space-y-2 overflow-y-auto subtle-scrollbar pr-1" aria-label="Transactions list">
          {transactions.map((tx) => (
            <li key={tx.id} className="flex items-center justify-between rounded-md border border-borderSoft/70 bg-panelSoft/40 px-3 py-2 text-sm">
              <span className="text-slate-200">{tx.label}</span>
              <span className={tx.type === 'income' ? 'text-emerald-300' : 'text-rose-300'}>
                {tx.type === 'income' ? '+' : '-'}${tx.amount.toFixed(2)}
              </span>
            </li>
          ))}
        </ul>
      </div>

      <aside className="flex flex-col gap-3">
        <div className="rounded-lg border border-borderSoft/70 bg-panel p-3 text-sm">
          <p className="text-slate-400">Income: <span className="text-emerald-300">${totals.income.toFixed(2)}</span></p>
          <p className="mt-1 text-slate-400">Expense: <span className="text-rose-300">${totals.expense.toFixed(2)}</span></p>
          <p className="mt-2 border-t border-borderSoft/70 pt-2 text-slate-300">Net: ${totals.net.toFixed(2)}</p>
        </div>

        <form onSubmit={addTransaction} className="rounded-lg border border-borderSoft/70 bg-panel p-3">
          <h3 className="text-xs uppercase tracking-[0.14em] text-slate-400">Add transaction</h3>
          <input
            aria-label="Transaction label"
            value={label}
            onChange={(event) => setLabel(event.target.value)}
            placeholder="Description"
            className="mt-2 w-full rounded-md border border-borderSoft/70 bg-panelSoft/70 px-3 py-2 text-sm text-slate-100 outline-none"
          />
          <input
            aria-label="Transaction amount"
            value={amount}
            onChange={(event) => setAmount(event.target.value)}
            placeholder="Amount"
            type="number"
            min="0"
            step="0.01"
            className="mt-2 w-full rounded-md border border-borderSoft/70 bg-panelSoft/70 px-3 py-2 text-sm text-slate-100 outline-none"
          />
          <select
            aria-label="Transaction type"
            value={type}
            onChange={(event) => setType(event.target.value as Transaction['type'])}
            className="mt-2 w-full rounded-md border border-borderSoft/70 bg-panelSoft/70 px-3 py-2 text-sm text-slate-100 outline-none"
          >
            <option value="expense">Expense</option>
            <option value="income">Income</option>
          </select>
          <button className="mt-3 w-full rounded-md border border-cyan-500/50 bg-cyan-500/10 px-3 py-2 text-xs text-cyan-100 hover:bg-cyan-500/20">
            Add transaction
          </button>
        </form>
      </aside>
    </section>
  );
}
