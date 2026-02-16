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
  XS: 'min-h-16',
  S: 'min-h-28',
  M: 'min-h-44',
  L: 'min-h-64',
  XL: 'min-h-[52vh]'
};

function TimelinePreview({ today, upcoming }: { today: VictusItem[]; upcoming: VictusItem[] }) {
  return (
    <div className="space-y-3 text-xs text-slate-300">
      <div>
        <p className="text-[10px] uppercase tracking-[0.2em] text-slate-500">Today</p>
        <ul className="mt-1 space-y-1">
          {today.slice(0, 4).map((event) => (
            <li key={event.id} className="truncate">{event.timeLabel} · {event.title}</li>
          ))}
        </ul>
      </div>
      <div>
        <p className="text-[10px] uppercase tracking-[0.2em] text-slate-500">Upcoming</p>
        <ul className="mt-1 space-y-1">
          {upcoming.slice(0, 3).map((event) => (
            <li key={event.id} className="truncate">{event.timeLabel} · {event.title}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function WorldTldrPreview({ expand }: { expand: boolean }) {
  const entries = expand ? worldTldrEntries : worldTldrEntries.slice(0, 2);
  return (
    <div className={`mt-2 space-y-2 text-xs text-slate-400 ${expand ? 'thin-scroll max-h-[46vh] overflow-y-auto pr-1' : ''}`}>
      {entries.map((entry) => (
        <p key={entry}>{entry}</p>
      ))}
    </div>
  );
}

function titleFor(id: string): string {
  if (id === 'systemOverview') return 'System Overview';
  if (id === 'dialogue') return 'Dialogue';
  if (id === 'timeline') return 'Timeline';
  if (id === 'worldTldr') return 'World TLDR';
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
      <div data-testid="center-stack" className="thin-scroll flex h-full flex-col gap-3 overflow-y-auto pr-1">
        {centerPlacements.map((placement, index) => renderCard(placement, index === 0, activeCard))}
      </div>
    </section>
  );

  function renderBody(id: string, isFocused: boolean): ReactNode {
    if (id === 'systemOverview') {
      return <SystemOverviewCard outcomes={outcomes} selectedId={selectedId} onSelect={onSelect} focusMode={isFocused} />;
    }
    if (id === 'dialogue') {
      const visible = isFocused ? dialogueMessages : dialogueMessages.slice(-2);
      return (
        <ul data-testid="dialogue-thread" className={`space-y-2 text-xs ${isFocused ? 'thin-scroll max-h-[44vh] overflow-y-auto pr-1' : ''}`}>
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
    return <WorldTldrPreview expand={isFocused} />;
  }

  function renderCard(placement: CardPlacement, isDominant: boolean, active?: string) {
    const isFocused = active === placement.id;
    const hasFocusMode = Boolean(active);

    return (
      <article
        key={placement.id}
        data-testid={`stack-card-${placement.id}`}
        data-focused={isFocused}
        className={`w-full rounded-xl border border-borderSoft/70 bg-panel px-4 py-3 transition-all duration-200 ${sizeTokens[placement.size]} ${isDominant ? 'ring-1 ring-cyan-500/25' : ''} ${placement.collapsed ? 'py-2' : ''} ${hasFocusMode && !isFocused ? 'opacity-80' : ''}`}
        onClick={() => onFocusCard(isFocused ? undefined : placement.id)}
      >
        <header className="flex items-center justify-between">
          <h2 className="text-sm font-medium text-slate-100">{titleFor(placement.id)}</h2>
          {!placement.collapsed && (
            <button
              className="text-xs text-slate-400 hover:text-slate-200"
              onClick={(event) => {
                event.stopPropagation();
                onFocusCard(isFocused ? undefined : placement.id);
              }}
            >
              {isFocused ? 'Collapse' : 'Expand'}
            </button>
          )}
        </header>
        {!placement.collapsed && <div className="mt-2">{renderBody(placement.id, isFocused)}</div>}
      </article>
    );
  }
}
