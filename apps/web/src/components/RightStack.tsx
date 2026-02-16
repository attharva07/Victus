import { useMemo, useState } from 'react';
import type { VictusCard, VictusItem } from '../data/victusStore';

const PREVIEW_COUNT = 2;

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

  const resolvedCards = useMemo(
    () => cards.map((card) => ({ ...card, entries: card.itemIds.map((id) => items[id]).filter(Boolean) })),
    [cards, items]
  );

  const focusedCard = resolvedCards.find((card) => card.kind === focusedKind) ?? null;

  return (
    <aside className="h-full overflow-hidden rounded-2xl border border-borderSoft/60 bg-panel/30 p-3">
      {!focusedCard ? (
        <div className="flex h-full flex-col gap-3 overflow-hidden">
          {resolvedCards.map((card) => {
            const previewItems = card.entries.slice(0, PREVIEW_COUNT);
            return (
              <section key={card.kind} className="min-h-0 flex-1 overflow-hidden rounded-xl border border-borderSoft/70 bg-panel px-3 py-2">
                <header className="flex items-center justify-between gap-2">
                  <button
                    className="truncate text-left text-xs uppercase tracking-[0.16em] text-slate-300 hover:text-slate-100"
                    onClick={() => setFocusedKind(card.kind)}
                  >
                    {card.title}
                  </button>
                  <button className="text-[11px] text-slate-400 hover:text-slate-200" onClick={() => setFocusedKind(card.kind)}>
                    Expand
                  </button>
                </header>

                <ul className="mt-2 space-y-1.5">
                  {previewItems.map((item) => (
                    <li key={item.id}>
                      <button
                        className={`w-full rounded-md px-2 py-1.5 text-left text-xs transition ${selectedId === item.id ? 'bg-cyan-500/10 text-cyan-100' : 'bg-panelSoft/50 text-slate-300 hover:bg-panelSoft/80'}`}
                        onClick={() => onSelect(item.id)}
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
      ) : (
        <section className="flex h-[calc(100vh-9.5rem)] min-h-0 flex-col rounded-xl border border-borderSoft/70 bg-panel px-3 py-2">
          <header className="flex items-center justify-between gap-2">
            <button className="truncate text-left text-xs uppercase tracking-[0.16em] text-slate-200 hover:text-white" onClick={() => setFocusedKind(null)}>
              ← Back
            </button>
            <h3 className="truncate text-xs uppercase tracking-[0.16em] text-slate-300">{focusedCard.title}</h3>
            <button className="text-[11px] text-slate-400 hover:text-slate-200" onClick={() => setFocusedKind(null)}>
              Collapse
            </button>
          </header>

          <ul data-testid="focused-rightstack-body" className="thin-scroll mt-2 min-h-0 flex-1 space-y-1.5 overflow-y-auto pr-1">
            {focusedCard.entries.map((item) => (
              <li key={item.id}>
                <button
                  className={`w-full rounded-md px-2 py-1.5 text-left text-xs transition ${selectedId === item.id ? 'bg-cyan-500/10 text-cyan-100' : 'bg-panelSoft/50 text-slate-300 hover:bg-panelSoft/80'}`}
                  onClick={() => onSelect(item.id)}
                >
                  <p className="truncate">{item.title}</p>
                  <p className="mt-0.5 text-[10px] uppercase tracking-wide text-slate-500">{contextMeta(item)}</p>
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}
    </aside>
  );
}
