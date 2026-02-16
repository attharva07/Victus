import type { VictusCard, VictusItem } from '../data/victusStore';

function contextMeta(item: VictusItem) {
  if (item.snoozedUntil) return `snoozed until ${item.snoozedUntil}`;
  if (item.kind === 'approval' && item.approvalState) return item.approvalState;
  if (item.kind === 'workflow' && item.workflowState) return item.workflowState;
  if (item.acknowledged) return 'acknowledged';
  if (item.muted) return 'muted';
  return item.timeLabel;
}

function ContextCard({
  card,
  items,
  selectedId,
  onToggle,
  onSelect
}: {
  card: VictusCard;
  items: VictusItem[];
  selectedId?: string;
  onToggle: () => void;
  onSelect: (id: string) => void;
}) {
  return (
    <section className="rounded-xl border border-borderSoft/80 bg-panel px-4 py-3">
      <button className="flex w-full items-center justify-between text-left" onClick={onToggle}>
        <span className="text-sm text-slate-100">{card.title}</span>
        <span className="rounded-full border border-borderSoft px-2 py-0.5 text-xs text-slate-400">{items.length}</span>
      </button>
      {!card.collapsed && (
        <ul className="mt-3 space-y-2 text-xs text-slate-300">
          {items.map((item) => (
            <li key={item.id}>
              <button
                onClick={() => onSelect(item.id)}
                className={`w-full rounded-md border border-borderSoft/50 bg-panelSoft/60 px-2 py-1.5 text-left transition hover:-translate-y-px hover:bg-slate-900/40 focus-visible:outline focus-visible:outline-2 focus-visible:outline-cyan-500 ${
                  selectedId === item.id ? 'ring-1 ring-cyan-400/60' : ''
                }`}
              >
                <p>{item.title}</p>
                <p className="mt-1 text-[10px] uppercase tracking-wide text-slate-500">{contextMeta(item)}</p>
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export default function ContextStack({
  cards,
  items,
  selectedId,
  onToggleCard,
  onSelect
}: {
  cards: VictusCard[];
  items: Record<string, VictusItem>;
  selectedId?: string;
  onToggleCard: (kind: VictusCard['kind']) => void;
  onSelect: (id: string) => void;
}) {
  return (
    <aside className="subtle-scrollbar h-full overflow-y-auto px-2 pb-20 pt-2">
      <div className="space-y-3">
        {cards.map((card) => (
          <ContextCard
            key={card.kind}
            card={card}
            items={card.itemIds.map((id) => items[id]).filter(Boolean)}
            selectedId={selectedId}
            onToggle={() => onToggleCard(card.kind)}
            onSelect={onSelect}
          />
        ))}
      </div>
    </aside>
  );
}
