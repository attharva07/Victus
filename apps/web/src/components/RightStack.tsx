import { useEffect, useMemo, useState } from 'react';
import type { VictusCard, VictusItem } from '../data/victusStore';

const PREVIEW_COUNT = 2;

const cardSizeTokens = {
  preview: 'h-24',
  focused: 'h-[48vh]',
  compressed: 'h-12'
};

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
  onSelect
}: {
  cards: VictusCard[];
  items: Record<string, VictusItem>;
  selectedId?: string;
  onSelect: (id: string) => void;
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

  const resolvedCards = useMemo(
    () => cards.map((card) => ({ ...card, entries: card.itemIds.map((id) => items[id]).filter(Boolean) })),
    [cards, items]
  );

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
                hasFocusMode ? (isFocused ? cardSizeTokens.focused : cardSizeTokens.compressed) : cardSizeTokens.preview
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
