import type { LayoutPlan } from '../layout/types';
import type { VictusCard, VictusItem } from '../data/victusStore';

const PREVIEW_COUNT = 2;

const cardSizeTokens = {
  XS: 'min-h-14',
  S: 'min-h-24',
  M: 'min-h-36',
  L: 'min-h-52',
  XL: 'min-h-[46vh]'
} as const;

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
  plan,
  focusedCardId,
  onFocusCard
}: {
  cards: VictusCard[];
  items: Record<string, VictusItem>;
  selectedId?: string;
  onSelect: (id: string) => void;
  plan: LayoutPlan;
  focusedCardId?: string;
  onFocusCard: (id?: string) => void;
}) {
  const cardsByKind = new Map(cards.map((card) => [card.kind, card]));

  const rightPlacements = plan.placements
    .filter((placement) => placement.zone === 'right')
    .sort((a, b) => a.priority - b.priority || a.id.localeCompare(b.id));

  return (
    <aside className="h-full overflow-hidden rounded-2xl border border-borderSoft/60 bg-panel/30 p-3">
      <div className="thin-scroll flex h-full flex-col gap-3 overflow-y-auto pr-1">
        {rightPlacements.map((placement) => {
          const card = cardsByKind.get(placement.id as VictusCard['kind']);
          if (!card) return null;

          const entries = card.itemIds.map((id) => items[id]).filter(Boolean);
          const isFocused = focusedCardId === placement.id;
          const visibleItems = isFocused ? entries : entries.slice(0, PREVIEW_COUNT);

          return (
            <section
              key={placement.id}
              data-testid={`right-stack-card-${placement.id}`}
              data-focused={isFocused}
              className={`min-h-0 overflow-hidden rounded-xl border border-borderSoft/70 bg-panel px-3 py-2 transition-all duration-200 ${cardSizeTokens[placement.size]}`}
              onClick={() => onFocusCard(isFocused ? undefined : placement.id)}
            >
              <header className="flex items-center justify-between gap-2">
                <h3 className="truncate text-left text-xs uppercase tracking-[0.16em] text-slate-300">{card.title}</h3>
                {!placement.collapsed && (
                  <button
                    className="text-[11px] text-slate-400 hover:text-slate-200"
                    onClick={(event) => {
                      event.stopPropagation();
                      onFocusCard(isFocused ? undefined : placement.id);
                    }}
                  >
                    {isFocused ? 'Collapse' : 'Expand'}
                  </button>
                )}
              </header>

              {!placement.collapsed && (
                <ul
                  data-testid={isFocused ? 'focused-rightstack-body' : undefined}
                  className={`mt-2 min-h-0 flex-1 space-y-1.5 pr-1 ${isFocused ? 'thin-scroll max-h-[40vh] overflow-y-auto' : 'overflow-hidden'}`}
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
              )}
            </section>
          );
        })}
      </div>
    </aside>
  );
}
