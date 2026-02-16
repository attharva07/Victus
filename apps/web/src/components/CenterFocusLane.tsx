import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import type { VictusItem } from '../data/victusStore';
import type { CardState, LayoutPlan, VictusCardId } from '../layout/types';
import { worldTldrEntries } from '../data/victusStore';
import type { LayoutSignals } from '../layout/signals';

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

function healthPulseAsStrip(signals: LayoutSignals): boolean {
  return signals.failuresSeverity !== 'high' && signals.failuresSeverity !== 'critical' && signals.confidenceScore >= 40;
}

function cardShellClass(state: CardState, id: VictusCardId): string {
  if (state === 'focus') {
    return id === 'dialogue'
      ? 'max-h-[55vh] min-h-[42vh]'
      : 'max-h-[48vh] min-h-[28vh]';
  }

  if (state === 'peek') {
    return 'max-h-44 min-h-28';
  }

  return 'min-h-0';
}

function LaneCard({
  id,
  state,
  onToggle,
  children
}: {
  id: VictusCardId;
  state: CardState;
  onToggle: () => void;
  children: ReactNode;
}) {
  const contentRef = useRef<HTMLDivElement>(null);
  const [contentOverflows, setContentOverflows] = useState(false);

  useEffect(() => {
    const node = contentRef.current;
    if (!node) return;

    const measure = () => {
      setContentOverflows(node.scrollHeight > node.clientHeight + 1);
    };

    measure();
    const raf = window.requestAnimationFrame(measure);
    window.addEventListener('resize', measure);

    return () => {
      window.cancelAnimationFrame(raf);
      window.removeEventListener('resize', measure);
    };
  }, [children, state]);

  return (
    <article
      data-testid={`center-card-${id}`}
      data-card-state={state}
      className={`w-full rounded-xl border border-borderSoft/70 bg-panel px-4 py-3 transition ${cardShellClass(state, id)} ${state === 'focus' ? 'ring-1 ring-cyan-500/30' : ''}`}
    >
      <header
        data-testid={`center-card-header-${id}`}
        className="flex cursor-pointer items-center justify-between gap-3"
        onClick={onToggle}
      >
        <h2 className="text-sm font-semibold text-slate-100">{titleFor(id)}</h2>
        <div className="flex items-center gap-2">
          {contentOverflows && state === 'peek' && (
            <button
              type="button"
              data-testid={`center-card-expand-${id}`}
              className="rounded border border-borderSoft/70 px-2 py-0.5 text-[10px] uppercase tracking-wide text-slate-300"
              onClick={(event) => {
                event.stopPropagation();
                onToggle();
              }}
            >
              Expand
            </button>
          )}
          <span className="text-[10px] uppercase tracking-[0.15em] text-slate-500">{state}</span>
        </div>
      </header>
      <div
        ref={contentRef}
        data-testid={`center-card-content-${id}`}
        className={`mt-3 ${state === 'focus' ? 'thin-scroll overflow-y-auto pr-1' : 'overflow-hidden'}`}
      >
        {children}
      </div>
    </article>
  );
}

function ChipRow({ ids, outcomes }: { ids: VictusCardId[]; outcomes: OutcomeBuckets }) {
  const counts: Partial<Record<VictusCardId, number>> = {
    failures: outcomes.failures.length,
    reminders: outcomes.reminders.length,
    approvals: outcomes.approvals.filter((item) => item.approvalState === 'pending').length,
    workflows: outcomes.workflows.length,
    alerts: outcomes.alerts.length
  };

  return (
    <div data-testid="chip-row" className="space-y-2 rounded-xl border border-borderSoft/70 bg-panel px-3 py-2">
      {ids.map((id) => (
        <div key={id} data-testid={`chip-row-item-${id}`} className="flex items-center justify-between rounded-md border border-borderSoft/70 bg-panelSoft/40 px-2 py-1 text-xs text-slate-300">
          <span>{titleFor(id)}</span>
          <span className="text-[10px] uppercase tracking-wide text-slate-500">active · {counts[id] ?? 0}</span>
        </div>
      ))}
    </div>
  );
}

export default function CenterFocusLane({
  plan,
  signals,
  today,
  upcoming,
  outcomes,
  dialogueMessages,
  onToggleCard
}: {
  plan: LayoutPlan;
  signals: LayoutSignals;
  today: VictusItem[];
  upcoming: VictusItem[];
  outcomes: OutcomeBuckets;
  dialogueMessages: DialogueMessage[];
  onToggleCard: (cardId: VictusCardId) => void;
}) {
  const dominantCardId = plan.dominantCardId ?? 'dialogue';
  const cardStates = plan.cardStates ?? {};
  const compactIds = plan.compactCardIds ?? [];
  const supportingCardIds = plan.supportingCardIds ?? [];
  const visibleSupporting = useMemo(() => supportingCardIds.slice(0, 4), [supportingCardIds]);

  return (
    <section className="h-full overflow-hidden rounded-2xl border border-borderSoft/60 bg-panel/45 p-3" aria-label="Center focus lane">
      <div data-testid="center-focus-lane" className="thin-scroll flex h-full flex-col gap-3 overflow-y-auto pr-1 pb-40">
        <LaneCard id={dominantCardId} state={cardStates[dominantCardId] ?? 'focus'} onToggle={() => onToggleCard(dominantCardId)}>
          {renderBody(dominantCardId, 'focus')}
        </LaneCard>

        {dominantCardId === 'dialogue' && healthPulseAsStrip(signals) && (
          <div data-testid="health-pulse-strip" className="rounded-lg border border-rose-900/50 bg-rose-950/20 px-3 py-2 text-xs text-rose-100">
            Health Pulse: {outcomes.failures.length} open failures · confidence {signals.confidenceScore}
          </div>
        )}

        {visibleSupporting
          .filter((cardId) => !(cardId === 'failures' && dominantCardId === 'dialogue' && healthPulseAsStrip(signals)))
          .map((cardId) => (
            <LaneCard key={cardId} id={cardId} state={cardStates[cardId] ?? 'peek'} onToggle={() => onToggleCard(cardId)}>
              {renderBody(cardId, 'peek')}
            </LaneCard>
          ))}

        {compactIds.length > 0 && <ChipRow ids={compactIds} outcomes={outcomes} />}
      </div>
    </section>
  );

  function renderBody(cardId: VictusCardId, state: CardState): ReactNode {
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
      const visible = state === 'peek' ? dialogueMessages.slice(-2) : dialogueMessages;
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
      const todayItems = state === 'peek' ? today.slice(0, 2) : today.slice(0, 4);
      const upcomingItems = state === 'peek' ? upcoming.slice(0, 1) : upcoming.slice(0, 3);
      return (
        <div className="space-y-2 text-xs text-slate-300">
          <p className="text-[10px] uppercase tracking-[0.15em] text-slate-500">Today</p>
          {todayItems.map((event) => (
            <p key={event.id}>{event.timeLabel} · {event.title}</p>
          ))}
          <p className="pt-2 text-[10px] uppercase tracking-[0.15em] text-slate-500">Upcoming</p>
          {upcomingItems.map((event) => (
            <p key={event.id}>{event.timeLabel} · {event.title}</p>
          ))}
        </div>
      );
    }

    if (cardId === 'worldTldr') {
      const entries = state === 'peek' ? worldTldrEntries.slice(0, 2) : worldTldrEntries;
      return (
        <div className="space-y-2 text-xs text-slate-300">
          {entries.map((entry) => (
            <p key={entry}>{entry}</p>
          ))}
        </div>
      );
    }

    const failureEntries = state === 'peek' ? outcomes.failures.slice(0, 3) : outcomes.failures;
    return (
      <ul className="space-y-2 text-xs text-rose-100">
        {failureEntries.length === 0 ? (
          <li className="text-slate-300">No unresolved failures.</li>
        ) : (
          failureEntries.map((failure) => (
            <li key={failure.id} className="rounded-md border border-rose-900/40 bg-rose-950/20 px-2 py-1">
              {failure.title}
            </li>
          ))
        )}
      </ul>
    );
  }
}
