import { useEffect, useMemo, useState } from 'react';
import type { VictusCard, VictusItem } from '../data/victusStore';
import type { CardPlacement, CardSize } from '../layout/types';

const PREVIEW_COUNT = 2;

const cardSizeTokens: Record<CardSize, string> = {
  XS: 'h-16',
  S: 'h-24',
  M: 'h-32',
  L: 'h-44',
  XL: 'h-[56vh]'
};

const focusedCardHeight = 'h-[48vh]';
const compressedCardHeight = 'h-12';

function contextMeta(item: VictusItem) {
  if (item.snoozedUntil) return `snoozed until ${item.snoozedUntil}`;
  if (item.kind === 'approval' && item.approvalState) return item.approvalState;
  if (item.kind === 'workflow' && item.workflowState) return item.workflowState;
  if (item.acknowledged) return 'acknowledged';
  if (item.muted) return 'muted';
  return item.timeLabel;
}

export default function RightStack({
  cards,
  items,
  selectedId,
  onSelect,
  placements,
  activeCardId
}: {
  cards: VictusCard[];
  items: Record<string, VictusItem>;
  selectedId?: string;
  onSelect: (id: string) => void;
  placements: CardPlacement[];
  activeCardId?: string;
}) {
  const [focusedKind, setFocusedKind] = useState<VictusCard['kind'] | null>(null);

  useEffect(() => {
    const onEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setFocusedKind(null);
      }
    };

    window.addEventListener('keydown', onEscape);
    return () => window.removeEventListener('keydown', onEscape);
  }, []);

  useEffect(() => {
    const rightKinds = new Set(placements.filter((placement) => placement.zone === 'right').map((placement) => placement.id));
    if (activeCardId && rightKinds.has(activeCardId)) {
      setFocusedKind(activeCardId as VictusCard['kind']);
    }
  }, [activeCardId, placements]);

  const resolvedCards = useMemo(() => {
    const byKind = cards.reduce<Record<string, VictusCard>>((acc, card) => {
      acc[card.kind] = card;
      return acc;
    }, {});

    return placements
      .filter((placement) => placement.zone === 'right')
      .sort((a, b) => a.priority - b.priority)
      .map((placement) => {
        const card = byKind[placement.id];
        if (!card) return null;

        return {
          ...card,
          size: placement.size,
          entries: card.itemIds.map((id) => items[id]).filter(Boolean)
        };
      })
      .filter((card): card is VictusCard & { size: CardSize; entries: VictusItem[] } => Boolean(card));
  }, [cards, items, placements]);

  const hasFocusMode = Boolean(focusedKind);

  return (
    <aside className="h-full overflow-hidden rounded-2xl border border-borderSoft/60 bg-panel/30 p-3">
      <div className="flex h-full flex-col gap-3 overflow-hidden">
        {resolvedCards.map((card) => {
          const isFocused = focusedKind === card.kind;
          const previewItems = card.entries.slice(0, PREVIEW_COUNT);
          const visibleItems = isFocused ? card.entries : previewItems;

          return (
            <section
              key={card.kind}
              data-testid={`right-stack-card-${card.kind}`}
              data-focused={isFocused}
              className={`min-h-0 overflow-hidden rounded-xl border border-borderSoft/70 bg-panel px-3 py-2 transition-all duration-300 ${
                hasFocusMode ? (isFocused ? focusedCardHeight : compressedCardHeight) : cardSizeTokens[card.size]
              }`}
              onClick={() => setFocusedKind((current) => (current === card.kind ? null : card.kind))}
            >
              <header className="flex items-center justify-between gap-2">
                <h3 className="truncate text-left text-xs uppercase tracking-[0.16em] text-slate-300">{card.title}</h3>
                <button
                  className="text-[11px] text-slate-400 hover:text-slate-200"
                  onClick={(event) => {
                    event.stopPropagation();
                    setFocusedKind((current) => (current === card.kind ? null : card.kind));
                  }}
                >
                  {isFocused ? 'Collapse' : 'Expand'}
                </button>
              </header>

              <ul
                data-testid={isFocused ? 'focused-rightstack-body' : undefined}
                className={`mt-2 min-h-0 flex-1 space-y-1.5 pr-1 ${isFocused ? 'thin-scroll h-[calc(100%-2.2rem)] overflow-y-auto' : 'overflow-hidden'}`}
              >
                {visibleItems.map((item) => (
                  <li key={item.id}>
                    <button
                      className={`w-full rounded-md px-2 py-1.5 text-left text-xs transition ${selectedId === item.id ? 'bg-cyan-500/10 text-cyan-100' : 'bg-panelSoft/50 text-slate-300 hover:bg-panelSoft/80'}`}
                      onClick={(event) => {
                        event.stopPropagation();
                        onSelect(item.id);
                      }}
                    >
                      <p className="truncate">{item.title}</p>
                      <p className="mt-0.5 text-[10px] uppercase tracking-wide text-slate-500">{contextMeta(item)}</p>
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          );
        })}
      </div>
    </aside>
  );
}
