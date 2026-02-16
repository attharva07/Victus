import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import type { VictusItem } from '../data/victusStore';
import type { LayoutPlan, VictusCardId } from '../layout/types';
import { worldTldrEntries } from '../data/victusStore';

type DialogueMessage = {
  id: string;
  role: 'user' | 'system';
  text: string;
};

type OutcomeBuckets = {
  reminders: VictusItem[];
  approvals: VictusItem[];
  workflows: VictusItem[];
  failures: VictusItem[];
  alerts: VictusItem[];
};

function titleFor(id: VictusCardId): string {
  if (id === 'systemOverview') return 'System Overview';
  if (id === 'dialogue') return 'Dialogue';
  if (id === 'timeline') return 'Timeline';
  if (id === 'worldTldr') return 'World TLDR';
  if (id === 'failures') return 'Health Pulse';
  if (id === 'reminders') return 'Reminders';
  if (id === 'approvals') return 'Approvals';
  if (id === 'alerts') return 'Alerts';
  return 'Workflows';
}

function LaneCard({
  id,
  dominant,
  expanded,
  onToggle,
  children
}: {
  id: VictusCardId;
  dominant?: boolean;
  expanded: boolean;
  onToggle: () => void;
  children: ReactNode;
}) {
  const contentRef = useRef<HTMLDivElement>(null);
  const [overflows, setOverflows] = useState(false);

  useEffect(() => {
    const el = contentRef.current;
    if (!el) return;
    const evaluate = () => setOverflows(el.scrollHeight > el.clientHeight + 6);
    evaluate();
    window.addEventListener('resize', evaluate);
    return () => window.removeEventListener('resize', evaluate);
  }, [children, expanded]);

  const minHeight = dominant ? (expanded ? 'min-h-[48vh]' : 'min-h-[38vh]') : expanded ? 'min-h-56' : 'min-h-36';

  return (
    <article
      data-testid={`center-card-${id}`}
      className={`w-full rounded-xl border border-borderSoft/70 bg-panel px-4 py-3 transition ${minHeight} ${dominant ? 'ring-1 ring-cyan-500/30' : ''}`}
      onClick={onToggle}
    >
      <header className="flex items-center justify-between gap-3">
        <h2 className="text-sm font-semibold text-slate-100">{titleFor(id)}</h2>
        {overflows && (
          <button
            className="text-xs text-slate-400 hover:text-slate-200"
            onClick={(event) => {
              event.stopPropagation();
              onToggle();
            }}
          >
            {expanded ? 'Collapse' : 'Expand'}
          </button>
        )}
      </header>
      <div ref={contentRef} className={`mt-3 ${expanded ? 'max-h-[65vh] overflow-y-auto thin-scroll pr-1' : 'max-h-40 overflow-hidden'}`}>
        {children}
      </div>
    </article>
  );
}

export default function CenterFocusLane({
  plan,
  today,
  upcoming,
  outcomes,
  dialogueMessages,
  expandedCardIds,
  onToggleCard
}: {
  plan: LayoutPlan;
  today: VictusItem[];
  upcoming: VictusItem[];
  outcomes: OutcomeBuckets;
  dialogueMessages: DialogueMessage[];
  expandedCardIds: Set<string>;
  onToggleCard: (cardId: string) => void;
}) {
  const compactIds = plan.compactCardIds;

  const visibleSupporting = useMemo(() => plan.supportingCardIds.slice(0, 4), [plan.supportingCardIds]);

  return (
    <section className="h-full overflow-hidden rounded-2xl border border-borderSoft/60 bg-panel/45 p-3" aria-label="Center focus lane">
      <div data-testid="center-focus-lane" className="thin-scroll flex h-full flex-col gap-3 overflow-y-auto pr-1 pb-40">
        <LaneCard
          id={plan.dominantCardId}
          dominant
          expanded={expandedCardIds.has(plan.dominantCardId)}
          onToggle={() => onToggleCard(plan.dominantCardId)}
        >
          {renderBody(plan.dominantCardId)}
        </LaneCard>

        {visibleSupporting.map((cardId) => (
          <LaneCard key={cardId} id={cardId} expanded={expandedCardIds.has(cardId)} onToggle={() => onToggleCard(cardId)}>
            {renderBody(cardId)}
          </LaneCard>
        ))}

        {compactIds.length > 0 && (
          <div className="rounded-xl border border-borderSoft/70 bg-panel px-3 py-2">
            <p className="text-[10px] uppercase tracking-[0.15em] text-slate-500">Compact</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {compactIds.map((id) => (
                <button
                  key={id}
                  data-testid={`compact-chip-${id}`}
                  className="rounded-full border border-borderSoft/70 bg-panelSoft/40 px-3 py-1 text-xs text-slate-300 hover:border-cyan-500/50"
                  onClick={() => onToggleCard(id)}
                >
                  {titleFor(id)}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </section>
  );

  function renderBody(cardId: VictusCardId): ReactNode {
    if (cardId === 'systemOverview') {
      return (
        <ul className="space-y-1 text-xs text-slate-300">
          <li>Reminders active: {outcomes.reminders.length}</li>
          <li>Approvals pending: {outcomes.approvals.filter((item) => item.approvalState === 'pending').length}</li>
          <li>Open failures: {outcomes.failures.filter((item) => item.status === 'active').length}</li>
          <li>Active workflows: {outcomes.workflows.length}</li>
        </ul>
      );
    }

    if (cardId === 'dialogue') {
      const visible = expandedCardIds.has(cardId) ? dialogueMessages : dialogueMessages.slice(-2);
      return (
        <ul className="space-y-2 text-xs">
          {visible.map((message) => (
            <li
              key={message.id}
              className={`rounded-lg border px-3 py-2 ${message.role === 'user' ? 'border-cyan-900/40 bg-cyan-950/20 text-cyan-100' : 'border-violet-900/50 bg-violet-950/15 text-slate-200'}`}
            >
              <p className="text-[10px] uppercase tracking-wide text-slate-500">{message.role}</p>
              <p className="mt-1">{message.text}</p>
            </li>
          ))}
        </ul>
      );
    }

    if (cardId === 'timeline') {
      return (
        <div className="space-y-2 text-xs text-slate-300">
          <p className="text-[10px] uppercase tracking-[0.15em] text-slate-500">Today</p>
          {today.slice(0, 4).map((event) => (
            <p key={event.id}>{event.timeLabel} · {event.title}</p>
          ))}
          <p className="pt-2 text-[10px] uppercase tracking-[0.15em] text-slate-500">Upcoming</p>
          {upcoming.slice(0, 3).map((event) => (
            <p key={event.id}>{event.timeLabel} · {event.title}</p>
          ))}
        </div>
      );
    }

    if (cardId === 'worldTldr') {
      const entries = expandedCardIds.has(cardId) ? worldTldrEntries : worldTldrEntries.slice(0, 2);
      return (
        <div className="space-y-2 text-xs text-slate-300">
          {entries.map((entry) => (
            <p key={entry}>{entry}</p>
          ))}
        </div>
      );
    }

    return (
      <ul className="space-y-2 text-xs text-rose-100">
        {outcomes.failures.length === 0 ? (
          <li className="text-slate-300">No unresolved failures.</li>
        ) : (
          outcomes.failures.map((failure) => (
            <li key={failure.id} className="rounded-md border border-rose-900/40 bg-rose-950/20 px-2 py-1">
              {failure.title}
            </li>
          ))
        )}
      </ul>
    );
  }
}
