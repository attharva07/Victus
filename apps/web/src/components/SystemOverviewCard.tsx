import { useMemo } from 'react';
import type { VictusItem } from '../data/victusStore';

function eventTone(type: VictusItem['type'], selected: boolean) {
  const base =
    type === 'user'
      ? 'border-cyan-700/35 bg-cyan-950/20 text-cyan-100'
      : 'border-violet-700/20 bg-violet-950/10 text-slate-200';

  return `${base} ${selected ? 'ring-1 ring-cyan-400/50' : ''}`;
}

function ordered(events: VictusItem[]) {
  return [...events].sort((a, b) => Number(b.type === 'user') - Number(a.type === 'user'));
}

function EventItem({ event, selected, onSelect }: { event: VictusItem; selected: boolean; onSelect: (id: string) => void }) {
  return (
    <li>
      <button
        className={`w-full rounded-lg border px-3 py-2 text-left transition hover:bg-slate-900/25 focus-visible:outline focus-visible:outline-2 focus-visible:outline-cyan-500 ${eventTone(event.type, selected)}`}
        onClick={() => onSelect(event.id)}
      >
        <div className="flex items-center justify-between text-xs uppercase tracking-wide text-slate-400">
          <span>{event.type}</span>
          <span>{event.timeLabel}</span>
        </div>
        <p className="mt-1 text-sm text-slate-100">{event.title}</p>
      </button>
    </li>
  );
}

function Section({ title, events, selectedId, onSelect, limit }: { title: string; events: VictusItem[]; selectedId?: string; onSelect: (id: string) => void; limit: number }) {
  const sortedEvents = useMemo(() => ordered(events), [events]);
  const visibleEvents = sortedEvents.slice(0, limit);

  return (
    <section className="space-y-2 border-b border-borderSoft/40 pb-3 last:border-b-0">
      <h3 className="text-[10px] font-semibold tracking-[0.2em] text-slate-400">{title}</h3>
      <ul className="space-y-2">
        {visibleEvents.map((event) => (
          <EventItem event={event} key={event.id} selected={selectedId === event.id} onSelect={onSelect} />
        ))}
      </ul>
    </section>
  );
}

export default function SystemOverviewCard({
  outcomes,
  selectedId,
  onSelect,
  focusMode = false
}: {
  outcomes: {
    reminders: VictusItem[];
    approvals: VictusItem[];
    workflows: VictusItem[];
    failures: VictusItem[];
    alerts: VictusItem[];
  };
  selectedId?: string;
  onSelect: (id: string) => void;
  focusMode?: boolean;
}) {
  const limits = focusMode ? 6 : 3;

  return (
    <div className={`space-y-3 ${focusMode ? 'thin-scroll max-h-[60vh] overflow-y-auto pr-1' : ''}`}>
      <Section title="REMINDERS CREATED / UPDATED" events={outcomes.reminders} selectedId={selectedId} onSelect={onSelect} limit={limits} />
      <Section title="APPROVALS PENDING / RESOLVED" events={outcomes.approvals} selectedId={selectedId} onSelect={onSelect} limit={limits} />
      <Section title="WORKFLOWS STARTED / COMPLETED" events={outcomes.workflows} selectedId={selectedId} onSelect={onSelect} limit={limits} />
      <Section title="FAILURES DETECTED / RESOLVED" events={outcomes.failures} selectedId={selectedId} onSelect={onSelect} limit={limits} />
      <Section title="ALERTS ACKNOWLEDGED / MUTED" events={outcomes.alerts} selectedId={selectedId} onSelect={onSelect} limit={limits} />
    </div>
  );
}
