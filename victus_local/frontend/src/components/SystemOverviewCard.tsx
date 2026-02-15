import { useMemo, useState } from 'react';
import { completedEvents, todayEvents, upcomingEvents, worldTldr, type TimelineEvent } from '../data/mockData';

function eventTone(type: TimelineEvent['type']) {
  return type === 'user'
    ? 'border-cyan-700/40 bg-cyan-950/30 text-cyan-100'
    : 'border-violet-700/30 bg-violet-950/20 text-slate-200';
}

function ordered(events: TimelineEvent[]) {
  return [...events].sort((a, b) => Number(b.type === 'user') - Number(a.type === 'user'));
}

function EventItem({ event }: { event: TimelineEvent }) {
  return (
    <li className={`rounded-lg border px-3 py-2 ${eventTone(event.type)}`}>
      <div className="flex items-center justify-between text-xs uppercase tracking-wide text-slate-400">
        <span className="flex items-center gap-2">
          <span className={`h-2 w-2 rounded-full ${event.type === 'user' ? 'bg-cyan-400' : 'bg-amber-300'}`} />
          {event.type}
        </span>
        <span>{event.timeLabel}</span>
      </div>
      <p className="mt-1 text-sm font-medium text-slate-100">{event.title}</p>
      <p className="mt-1 text-xs text-slate-400">{event.detail}</p>
    </li>
  );
}

function Section({
  title,
  events,
  expandable,
  defaultPreview = 3
}: {
  title: string;
  events: TimelineEvent[];
  expandable?: boolean;
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
          <EventItem event={event} key={event.id} />
        ))}
      </ul>
    </section>
  );
}

export default function SystemOverviewCard() {
  return (
    <article className="rounded-xl border border-borderSoft/80 bg-panel p-5 shadow-sm shadow-black/30">
      <h2 className="text-lg font-medium text-slate-100">System Overview</h2>
      <div className="mt-4 space-y-4">
        <Section title="TODAY" events={todayEvents} />
        <Section title="UPCOMING" events={upcomingEvents} expandable defaultPreview={2} />
        <Section title="COMPLETED" events={completedEvents} expandable defaultPreview={2} />
      </div>
      <div className="mt-4 rounded-lg border border-borderSoft/50 bg-panelSoft/70 p-3">
        <h3 className="text-[10px] tracking-[0.2em] text-slate-500">WORLD TLDR</h3>
        <ul className="mt-2 space-y-2 text-xs text-slate-400">
          {worldTldr.map((entry) => (
            <li key={entry}>{entry}</li>
          ))}
        </ul>
      </div>
    </article>
  );
}
