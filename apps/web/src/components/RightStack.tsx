import { useMemo, useState } from 'react';
import type { VictusCard, VictusItem } from '../data/victusStore';
import type { CardSize } from '../layout/types';

const sizeTokens: Record<CardSize, string> = {
  XS: 'h-24',
  S: 'h-36',
  M: 'h-48',
  L: 'h-64',
  XL: 'h-[66vh]'
};

function contextMeta(item: VictusItem) {
  if (item.snoozedUntil) return `snoozed until ${item.snoozedUntil}`;
  if (item.kind === 'approval' && item.approvalState) return item.approvalState;
  if (item.kind === 'workflow' && item.workflowState) return item.workflowState;
  if (item.acknowledged) return 'acknowledged';
  if (item.muted) return 'muted';
  return item.timeLabel;
}

function byKindSize(kind: VictusCard['kind']): CardSize {
  if (kind === 'approvals') return 'XS';
  return 'S';
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

  return (
    <aside className="h-full rounded-2xl border border-borderSoft/60 bg-panel/30 p-3">
      <div className="space-y-3">
        {resolvedCards.map((card) => {
          const focused = focusedKind === card.kind;
          const previewItems = card.entries.slice(0, 3);
          const visibleItems = focused ? card.entries : previewItems;

          return (
            <section
              key={card.kind}
              className={`rounded-xl border border-borderSoft/70 bg-panel px-3 py-2 transition-all duration-300 ${
                focusedKind ? (focused ? sizeTokens.XL : 'h-16 overflow-hidden opacity-75') : sizeTokens[byKindSize(card.kind)]
              }`}
            >
              <header className="flex items-center justify-between gap-2">
                <h3 className="text-xs uppercase tracking-[0.16em] text-slate-300">{card.title}</h3>
                <button className="text-[11px] text-slate-400 hover:text-slate-200" onClick={() => setFocusedKind((current) => (current === card.kind ? null : card.kind))}>
                  {focused ? 'Collapse' : 'Expand'}
                </button>
              </header>

              <ul className={`mt-2 space-y-1.5 ${focused ? 'thin-scroll max-h-[56vh] overflow-y-auto pr-1' : 'overflow-hidden'}`}>
                {visibleItems.map((item) => (
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
    </aside>
  );
}
