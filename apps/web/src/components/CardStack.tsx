import { type ReactNode } from 'react';
import type { LayoutPlan, CardPlacement, CardSize } from '../layout/types';
import SystemOverviewCard from './SystemOverviewCard';
import type { VictusItem } from '../data/victusStore';
import { worldTldrEntries } from '../data/victusStore';

type DialogueMessage = {
  id: string;
  role: 'user' | 'system';
  text: string;
};

const sizeTokens: Record<CardSize, string> = {
  XS: 'h-20',
  S: 'h-32',
  M: 'h-48',
  L: 'h-64',
  XL: 'h-[72vh]'
};

const compressedStrip = 'h-12';

function TimelinePreview({ today, upcoming }: { today: VictusItem[]; upcoming: VictusItem[] }) {
  return (
    <div className="space-y-3 text-xs text-slate-300">
      <div>
        <p className="text-[10px] uppercase tracking-[0.2em] text-slate-500">Today</p>
        <ul className="mt-1 space-y-1">
          {today.slice(0, 3).map((event) => (
            <li key={event.id} className="truncate">{event.timeLabel} · {event.title}</li>
          ))}
        </ul>
      </div>
      <div>
        <p className="text-[10px] uppercase tracking-[0.2em] text-slate-500">Upcoming</p>
        <ul className="mt-1 space-y-1">
          {upcoming.slice(0, 2).map((event) => (
            <li key={event.id} className="truncate">{event.timeLabel} · {event.title}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function WorldTldrPreview({ focusMode }: { focusMode: boolean }) {
  const entries = focusMode ? worldTldrEntries : worldTldrEntries.slice(0, 2);

  return (
    <div className={`mt-2 space-y-2 text-xs text-slate-400 ${focusMode ? 'thin-scroll max-h-[58vh] overflow-y-auto pr-1' : ''}`}>
      {entries.map((entry) => (
        <p key={entry}>{entry}</p>
      ))}
    </div>
  );
}

function titleFor(id: string): string {
  if (id === 'system_overview') return 'System Overview';
  if (id === 'dialogue') return 'Dialogue';
  if (id === 'timeline') return 'Timeline';
  if (id === 'world_tldr') return 'World TLDR';
  return id;
}

export default function CardStack({
  today,
  upcoming,
  outcomes,
  dialogueMessages,
  selectedId,
  onSelect,
  plan,
  focusedCardId,
  onFocusCard
}: {
  today: VictusItem[];
  upcoming: VictusItem[];
  outcomes: {
    reminders: VictusItem[];
    approvals: VictusItem[];
    workflows: VictusItem[];
    failures: VictusItem[];
    alerts: VictusItem[];
  };
  dialogueMessages: DialogueMessage[];
  selectedId?: string;
  onSelect: (id: string) => void;
  plan: LayoutPlan;
  focusedCardId?: string;
  onFocusCard: (id?: string) => void;
}) {
  const centerPlacements = plan.placements
    .filter((placement) => placement.zone === 'center')
    .sort((a, b) => a.priority - b.priority || a.id.localeCompare(b.id));

  const activeCard = focusedCardId ?? plan.activeCardId;

  return (
    <section className="relative h-full overflow-hidden rounded-2xl border border-borderSoft/60 bg-panel/45 p-3" aria-label="Center Card Stack">
      <div data-testid="center-grid" className="grid h-full grid-cols-2 gap-4 overflow-hidden">
        {centerPlacements.map((placement) => renderCard(placement, activeCard))}
      </div>
    </section>
  );

  function renderBody(id: string, isFocused: boolean): ReactNode {
    if (id === 'system_overview') {
      return <SystemOverviewCard outcomes={outcomes} selectedId={selectedId} onSelect={onSelect} focusMode={isFocused} />;
    }
    if (id === 'dialogue') {
      const visible = isFocused ? dialogueMessages : dialogueMessages.slice(-2);
      return (
        <ul data-testid="dialogue-thread" className={`space-y-2 text-xs ${isFocused ? 'thin-scroll max-h-[58vh] overflow-y-auto pr-1' : ''}`}>
          {visible.map((message) => (
            <li key={message.id} className={`rounded-lg border px-3 py-2 ${message.role === 'user' ? 'border-cyan-800/40 bg-cyan-950/20 text-cyan-100' : 'border-violet-900/40 bg-violet-950/20 text-slate-200'}`}>
              <p className="text-[10px] uppercase tracking-[0.16em] text-slate-400">{message.role}</p>
              <p className="mt-1 text-sm">{message.text}</p>
            </li>
          ))}
        </ul>
      );
    }
    if (id === 'timeline') {
      return <TimelinePreview today={today} upcoming={upcoming} />;
    }
    return <WorldTldrPreview focusMode={isFocused} />;
  }

  function renderCard(placement: CardPlacement, active?: string) {
    const isFocused = active === placement.id;
    const hasFocusMode = Boolean(active);
    const heightClass = hasFocusMode ? (isFocused ? sizeTokens.XL : compressedStrip) : sizeTokens[placement.size];

    return (
      <article
        key={placement.id}
        data-testid={`stack-card-${placement.id}`}
        data-focused={isFocused}
        style={{ gridColumn: `span ${placement.colSpan} / span ${placement.colSpan}` }}
        className={`min-h-0 rounded-xl border border-borderSoft/70 bg-panel px-4 py-3 transition-all duration-300 ${heightClass} ${plan.activeCardId === placement.id ? 'ring-1 ring-cyan-400/35' : ''} ${hasFocusMode && !isFocused ? 'overflow-hidden opacity-80' : 'overflow-hidden'}`}
        onClick={() => onFocusCard(isFocused ? undefined : placement.id)}
      >
        <header className="flex items-center justify-between">
          <h2 className="text-sm font-medium text-slate-100">{titleFor(placement.id)}</h2>
          <button
            className="text-xs text-slate-400 hover:text-slate-200"
            onClick={(event) => {
              event.stopPropagation();
              onFocusCard(isFocused ? undefined : placement.id);
            }}
          >
            {isFocused ? 'Collapse' : 'Expand'}
          </button>
        </header>
        <div className={`mt-2 ${isFocused ? 'thin-scroll h-[calc(100%-2.25rem)] overflow-y-auto pr-1' : 'overflow-hidden'}`}>
          {renderBody(placement.id, isFocused)}
        </div>
      </article>
    );
  }
}
