import { useMemo, useState } from 'react';
import type { VictusItem } from '../data/victusStore';
import { worldTldrEntries } from '../data/victusStore';

function eventTone(type: VictusItem['type'], selected: boolean) {
  const base =
    type === 'user'
      ? 'border-cyan-700/40 bg-cyan-950/30 text-cyan-100'
      : 'border-violet-700/30 bg-violet-950/20 text-slate-200';

  return `${base} ${selected ? 'ring-1 ring-cyan-400/60' : ''}`;
}

function ordered(events: VictusItem[]) {
  return [...events].sort((a, b) => Number(b.type === 'user') - Number(a.type === 'user'));
}

function EventItem({
  event,
  selected,
  onSelect
}: {
  event: VictusItem;
  selected: boolean;
  onSelect: (id: string) => void;
}) {
  return (
    <li>
      <button
        className={`w-full rounded-lg border px-3 py-2 text-left transition hover:-translate-y-px hover:bg-slate-900/30 focus-visible:outline focus-visible:outline-2 focus-visible:outline-cyan-500 ${eventTone(event.type, selected)}`}
        onClick={() => onSelect(event.id)}
      >
        <div className="flex items-center justify-between text-xs uppercase tracking-wide text-slate-400">
          <span className="flex items-center gap-2">
            <span className={`h-2 w-2 rounded-full ${event.type === 'user' ? 'bg-cyan-400' : 'bg-amber-300'}`} />
            {event.type}
            {event.acknowledged ? <span className="text-[10px] text-emerald-300">ack</span> : null}
          </span>
          <span>{event.timeLabel}</span>
        </div>
        <p className="mt-1 text-sm font-medium text-slate-100">{event.title}</p>
        <p className="mt-1 text-xs text-slate-400">{event.detail}</p>
      </button>
    </li>
  );
}

function Section({
  title,
  events,
  expandable,
  selectedId,
  onSelect,
  defaultPreview = 3
}: {
  title: string;
  events: VictusItem[];
  expandable?: boolean;
  selectedId?: string;
  onSelect: (id: string) => void;
  defaultPreview?: number;
}) {
  const [expanded, setExpanded] = useState(false);
  const sortedEvents = useMemo(() => ordered(events), [events]);
  const visibleEvents = expandable && !expanded ? sortedEvents.slice(0, defaultPreview) : sortedEvents;

  return (
    <section className="space-y-2 border-b border-borderSoft/40 pb-4 last:border-b-0">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-semibold tracking-[0.24em] text-slate-400">{title}</h3>
        {expandable && (
          <button className="text-xs text-slate-400 hover:text-slate-200" onClick={() => setExpanded((s) => !s)}>
            {expanded ? 'Collapse' : 'View All'}
          </button>
        )}
      </div>
      <ul className="space-y-2">
        {visibleEvents.map((event) => (
          <EventItem event={event} key={event.id} selected={selectedId === event.id} onSelect={onSelect} />
        ))}
      </ul>
    </section>
  );
}

export default function SystemOverviewCard({
  today,
  upcoming,
  completed,
  selectedId,
  onSelect
}: {
  today: VictusItem[];
  upcoming: VictusItem[];
  completed: VictusItem[];
  selectedId?: string;
  onSelect: (id: string) => void;
}) {
  return (
    <article className="rounded-xl border border-borderSoft/80 bg-panel p-5 shadow-sm shadow-black/30">
      <h2 className="text-lg font-medium text-slate-100">System Overview</h2>
      <div className="mt-4 space-y-4">
        <Section title="TODAY" events={today} selectedId={selectedId} onSelect={onSelect} />
        <Section title="UPCOMING" events={upcoming} selectedId={selectedId} onSelect={onSelect} expandable defaultPreview={2} />
        <Section title="COMPLETED" events={completed} selectedId={selectedId} onSelect={onSelect} expandable defaultPreview={2} />
      </div>
      <div className="mt-4 rounded-lg border border-borderSoft/50 bg-panelSoft/70 p-3">
        <h3 className="text-[10px] tracking-[0.2em] text-slate-500">WORLD TLDR</h3>
        <ul className="mt-2 space-y-2 text-xs text-slate-400">
          {worldTldrEntries.map((entry) => (
            <li key={entry}>{entry}</li>
          ))}
        </ul>
      </div>
    </article>
  );
}
