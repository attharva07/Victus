import { useEffect, useMemo, useState, type ReactNode } from 'react';
import type { CardSize } from '../layout/types';
import SystemOverviewCard from './SystemOverviewCard';
import type { VictusItem } from '../data/victusStore';
import { worldTldrEntries } from '../data/victusStore';

type StackCard = {
  id: string;
  title: string;
  size: CardSize;
  render: (focusMode: boolean) => ReactNode;
};

type DialogueMessage = {
  id: string;
  role: 'user' | 'system';
  text: string;
};

const sizeTokens: Record<CardSize, string> = {
  XS: 'h-16',
  S: 'h-28',
  M: 'h-44',
  L: 'h-64',
  XL: 'h-[72vh]'
};

const compressedStrip = 'h-12';

function TimelinePreview({ today, upcoming }: { today: VictusItem[]; upcoming: VictusItem[] }) {
  const topToday = today.slice(0, 3);
  const nextUp = upcoming.slice(0, 2);

  return (
    <div className="space-y-3 text-xs text-slate-300">
      <div>
        <p className="text-[10px] uppercase tracking-[0.2em] text-slate-500">Today</p>
        <ul className="mt-1 space-y-1">
          {topToday.map((event) => (
            <li key={event.id} className="truncate">{event.timeLabel} · {event.title}</li>
          ))}
        </ul>
      </div>
      <div>
        <p className="text-[10px] uppercase tracking-[0.2em] text-slate-500">Upcoming</p>
        <ul className="mt-1 space-y-1">
          {nextUp.map((event) => (
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

export default function CardStack({
  today,
  upcoming,
  outcomes,
  dialogueMessages,
  dialogueOpen,
  selectedId,
  onSelect
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
  dialogueOpen: boolean;
  selectedId?: string;
  onSelect: (id: string) => void;
}) {
  const [activeIndex, setActiveIndex] = useState(0);
  const [focusedCardId, setFocusedCardId] = useState<string | null>(null);

  useEffect(() => {
    const onEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setFocusedCardId(null);
      }
    };

    window.addEventListener('keydown', onEscape);
    return () => window.removeEventListener('keydown', onEscape);
  }, []);

  useEffect(() => {
    if (dialogueOpen) {
      setFocusedCardId('dialogue');
    }
  }, [dialogueOpen]);

  const cards = useMemo<StackCard[]>(
    () => [
      {
        id: 'system_overview',
        title: 'System Overview',
        size: 'L',
        render: (focusMode) => (
          <SystemOverviewCard
            outcomes={outcomes}
            selectedId={selectedId}
            onSelect={onSelect}
            focusMode={focusMode}
          />
        )
      },
      {
        id: 'dialogue',
        title: 'Dialogue',
        size: 'S',
        render: (focusMode) => {
          const visible = focusMode ? dialogueMessages : dialogueMessages.slice(-2);
          return (
            <ul data-testid="dialogue-thread" className={`space-y-2 text-xs ${focusMode ? 'thin-scroll max-h-[58vh] overflow-y-auto pr-1' : ''}`}>
              {visible.map((message) => (
                <li
                  key={message.id}
                  className={`rounded-lg border px-3 py-2 ${message.role === 'user' ? 'border-cyan-800/40 bg-cyan-950/20 text-cyan-100' : 'border-violet-900/40 bg-violet-950/20 text-slate-200'}`}
                >
                  <p className="text-[10px] uppercase tracking-[0.16em] text-slate-400">{message.role}</p>
                  <p className="mt-1 text-sm">{message.text}</p>
                </li>
              ))}
            </ul>
          );
        }
      },
      {
        id: 'timeline',
        title: 'Timeline',
        size: 'M',
        render: () => <TimelinePreview today={today} upcoming={upcoming} />
      },
      {
        id: 'world_tldr',
        title: 'World TLDR',
        size: 'S',
        render: (focusMode) => <WorldTldrPreview focusMode={focusMode} />
      }
    ],
    [dialogueMessages, onSelect, outcomes, selectedId, today, upcoming]
  );

  const shiftActive = (delta: number) => {
    setActiveIndex((current) => {
      const next = Math.max(0, Math.min(cards.length - 1, current + delta));
      return next;
    });
  };

  return (
    <section
      className="relative h-full overflow-hidden rounded-2xl border border-borderSoft/60 bg-panel/45 p-3"
      onWheel={(event) => {
        event.preventDefault();
        if (focusedCardId) return;
        shiftActive(event.deltaY > 0 ? 1 : -1);
      }}
      onKeyDown={(event) => {
        if (event.key === 'j' || event.key === 'ArrowDown') {
          event.preventDefault();
          shiftActive(1);
        }
        if (event.key === 'k' || event.key === 'ArrowUp') {
          event.preventDefault();
          shiftActive(-1);
        }
      }}
      tabIndex={0}
      aria-label="Center Card Stack"
    >
      <div className={`h-full space-y-3 transition-transform duration-300 ${focusedCardId ? '' : ''}`} style={focusedCardId ? undefined : { transform: `translateY(-${activeIndex * 72}px)` }}>
        {cards.map((card, index) => {
          const isFocused = focusedCardId === card.id;
          const hasFocusMode = Boolean(focusedCardId);
          const isActive = index === activeIndex;

          return (
            <article
              key={card.id}
              data-testid={`stack-card-${card.id}`}
              data-active={isActive}
              data-focused={isFocused}
              className={`rounded-xl border border-borderSoft/70 bg-panel px-4 py-3 transition-all duration-300 ${
                hasFocusMode ? (isFocused ? `${sizeTokens.XL}` : compressedStrip) : sizeTokens[card.size]
              } ${isActive ? 'ring-1 ring-cyan-400/35' : ''} ${hasFocusMode && !isFocused ? 'overflow-hidden opacity-80' : 'overflow-hidden'}`}
              onClick={() => setFocusedCardId((current) => (current === card.id ? null : card.id))}
            >
              <header className="flex items-center justify-between">
                <h2 className="text-sm font-medium text-slate-100">{card.title}</h2>
                <button
                  className="text-xs text-slate-400 hover:text-slate-200"
                  onClick={(event) => {
                    event.stopPropagation();
                    setFocusedCardId((current) => (current === card.id ? null : card.id));
                  }}
                >
                  {isFocused ? 'Collapse' : 'Expand'}
                </button>
              </header>
              <div className={`mt-2 ${isFocused ? 'thin-scroll h-[calc(100%-2.25rem)] overflow-y-auto pr-1' : 'overflow-hidden'}`}>{card.render(isFocused)}</div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
