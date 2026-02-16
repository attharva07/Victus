import { useState } from 'react';
import { contextCards } from '../data/mockData';

function ContextCard({ title, count, items }: { title: string; count: number; items: { id: string; label: string; meta?: string }[] }) {
  const [open, setOpen] = useState(true);

  return (
    <section className="rounded-xl border border-borderSoft/80 bg-panel px-4 py-3">
      <button className="flex w-full items-center justify-between text-left" onClick={() => setOpen((s) => !s)}>
        <span className="text-sm text-slate-100">{title}</span>
        <span className="rounded-full border border-borderSoft px-2 py-0.5 text-xs text-slate-400">{count}</span>
      </button>
      {open && (
        <ul className="mt-3 space-y-2 text-xs text-slate-300">
          {items.map((item) => (
            <li key={item.id} className="rounded-md border border-borderSoft/50 bg-panelSoft/60 px-2 py-1.5">
              <p>{item.label}</p>
              {item.meta ? <p className="mt-1 text-[10px] uppercase tracking-wide text-slate-500">{item.meta}</p> : null}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export default function ContextStack() {
  return (
    <aside className="h-full overflow-y-auto px-2 pb-20 pt-2">
      <div className="space-y-3">
        {contextCards.map((card) => (
          <ContextCard key={card.id} title={card.title} count={card.items.length} items={card.items} />
        ))}
      </div>
    </aside>
  );
}
