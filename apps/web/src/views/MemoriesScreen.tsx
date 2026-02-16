import { useMemo, useState } from 'react';

type MemoryItem = {
  id: string;
  title: string;
  content: string;
  tags: string[];
  createdAt: string;
  pinned: boolean;
  deleted: boolean;
};

const initialMemories: MemoryItem[] = [
  {
    id: 'm-1',
    title: 'Q2 Planning Principles',
    content: 'Bias for fewer goals and stronger execution loops. Keep weekly confidence check-ins visible.',
    tags: ['planning', 'strategy'],
    createdAt: '2026-02-09 09:30',
    pinned: true,
    deleted: false
  },
  {
    id: 'm-2',
    title: 'Infra incident follow-up',
    content: 'Documented the fallback routing decision and captured owner checklist for recurrence prevention.',
    tags: ['infra', 'incident'],
    createdAt: '2026-02-12 15:40',
    pinned: false,
    deleted: false
  },
  {
    id: 'm-3',
    title: 'Finance weekly digest note',
    content: 'Spending remained flat week-over-week, main variance from contractor tooling.',
    tags: ['finance'],
    createdAt: '2026-02-14 11:05',
    pinned: false,
    deleted: false
  }
];

export default function MemoriesScreen() {
  const [query, setQuery] = useState('');
  const [memories, setMemories] = useState<MemoryItem[]>(initialMemories);
  const [selectedId, setSelectedId] = useState(initialMemories[0]?.id ?? null);

  const visibleMemories = useMemo(() => {
    const lowered = query.trim().toLowerCase();
    return memories.filter((item) => {
      if (item.deleted) return false;
      if (!lowered) return true;
      return `${item.title} ${item.content} ${item.tags.join(' ')}`.toLowerCase().includes(lowered);
    });
  }, [memories, query]);

  const selected = memories.find((item) => item.id === selectedId && !item.deleted) ?? visibleMemories[0] ?? null;

  return (
    <section className="grid h-full grid-cols-[minmax(0,320px)_minmax(0,1fr)] gap-3 rounded-xl border border-borderSoft/80 bg-panel/60 p-3">
      <div className="flex min-h-0 flex-col rounded-lg border border-borderSoft/70 bg-panel px-3 py-2">
        <label htmlFor="memory-search" className="text-xs uppercase tracking-[0.14em] text-slate-400">
          Search memories
        </label>
        <input
          id="memory-search"
          placeholder="Filter by keyword"
          className="mt-2 rounded-md border border-borderSoft/70 bg-panelSoft/80 px-3 py-2 text-sm text-slate-100 outline-none placeholder:text-slate-500 focus:border-cyan-500/60"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />

        <ul className="mt-3 min-h-0 flex-1 space-y-2 overflow-y-auto subtle-scrollbar pr-1" aria-label="Memory results">
          {visibleMemories.map((memory) => (
            <li key={memory.id}>
              <button
                className={`w-full rounded-md border px-3 py-2 text-left text-sm transition ${selected?.id === memory.id ? 'border-cyan-500/60 bg-cyan-500/10 text-cyan-100' : 'border-borderSoft/70 bg-panelSoft/40 text-slate-300 hover:bg-panelSoft/70'}`}
                onClick={() => setSelectedId(memory.id)}
              >
                <p className="truncate font-medium">{memory.title}</p>
                <p className="mt-1 text-xs text-slate-500">{memory.tags.join(' · ')}</p>
              </button>
            </li>
          ))}
          {visibleMemories.length === 0 && <li className="rounded-md border border-dashed border-borderSoft/60 p-3 text-sm text-slate-500">No memories match this search.</li>}
        </ul>
      </div>

      <article className="flex min-h-0 flex-col rounded-lg border border-borderSoft/70 bg-panel p-4">
        {selected ? (
          <>
            <header>
              <h2 className="text-base font-medium text-slate-100">{selected.title}</h2>
              <p className="mt-1 text-xs text-slate-500">{selected.createdAt} · {selected.tags.join(', ')}</p>
            </header>
            <p className="mt-4 flex-1 overflow-y-auto subtle-scrollbar pr-2 text-sm leading-relaxed text-slate-300">{selected.content}</p>
            <div className="mt-4 flex flex-wrap gap-2">
              <button
                className="rounded-md border border-borderSoft/70 px-3 py-1.5 text-xs text-slate-300 hover:bg-panelSoft/70"
                onClick={() =>
                  setMemories((prev) => prev.map((item) => (item.id === selected.id ? { ...item, deleted: true } : item)))
                }
              >
                Delete
              </button>
              <button
                className="rounded-md border border-borderSoft/70 px-3 py-1.5 text-xs text-slate-300 hover:bg-panelSoft/70"
                onClick={() =>
                  setMemories((prev) => prev.map((item) => (item.id === selected.id ? { ...item, pinned: !item.pinned } : item)))
                }
              >
                {selected.pinned ? 'Unpin' : 'Pin'}
              </button>
              <button
                className="rounded-md border border-borderSoft/70 px-3 py-1.5 text-xs text-slate-300 hover:bg-panelSoft/70"
                onClick={() => setQuery(selected.title)}
              >
                Copy
              </button>
            </div>
          </>
        ) : (
          <div className="flex h-full items-center justify-center text-sm text-slate-500">Select a memory to inspect details.</div>
        )}
      </article>
    </section>
  );
}
