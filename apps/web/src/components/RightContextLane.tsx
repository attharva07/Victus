import { useState } from 'react';
import type { VictusCard, VictusItem } from '../data/victusStore';
import type { VictusCardId } from '../layout/types';

type ContextActionHandlers = {
  onMarkReminderDone: (id: string) => void;
  onApprove: (id: string) => void;
  onDeny: (id: string) => void;
  onAcknowledgeAlert: (id: string) => void;
};

const titleMap: Record<VictusCardId, string> = {
  failures: 'Failures',
  approvals: 'Approvals',
  alerts: 'Alerts',
  reminders: 'Reminders',
  workflows: 'Workflows',
  systemOverview: 'System Overview',
  dialogue: 'Dialogue',
  timeline: 'Timeline',
  worldTldr: 'World TLDR'
};

export default function RightContextLane({
  orderedCardIds,
  cards,
  items,
  highlightedId,
  onHighlight,
  actions
}: {
  orderedCardIds: VictusCardId[];
  cards: VictusCard[];
  items: Record<string, VictusItem>;
  highlightedId?: string;
  onHighlight: (id?: string) => void;
  actions: ContextActionHandlers;
}) {
  const [expandedCardId, setExpandedCardId] = useState<string | undefined>();

  return (
    <aside className="h-full overflow-hidden rounded-2xl border border-borderSoft/60 bg-panel/30 p-3">
      <div data-testid="right-context-scroll" className="thin-scroll flex h-full flex-col gap-3 overflow-y-auto pr-1 pb-24">
        {orderedCardIds.map((cardId) => {
          const card = cards.find((entry) => entry.kind === cardId);
          if (!card) return null;

          const isExpanded = expandedCardId === cardId;
          const cardItems = card.itemIds.map((id) => items[id]).filter(Boolean);
          const visibleItems = isExpanded ? cardItems : cardItems.slice(0, 2);

          return (
            <section
              key={cardId}
              data-testid={`right-context-card-${cardId}`}
              className={`rounded-xl border border-borderSoft/70 bg-panel px-3 py-2 ${isExpanded ? 'min-h-56' : 'min-h-28'}`}
              onClick={() => setExpandedCardId(isExpanded ? undefined : cardId)}
            >
              <header className="flex items-center justify-between gap-2">
                <h3 className="text-xs uppercase tracking-[0.15em] text-slate-300">{titleMap[cardId]}</h3>
                <p className="text-[10px] text-slate-500">{cardItems.length} items</p>
              </header>

              <ul className={`mt-2 space-y-2 ${isExpanded ? 'thin-scroll max-h-[50vh] overflow-y-auto pr-1' : ''}`}>
                {visibleItems.map((item) => {
                  const highlighted = highlightedId === item.id;
                  return (
                    <li key={item.id}>
                      <button
                        className={`w-full rounded-md border px-2 py-1.5 text-left ${highlighted ? 'border-cyan-500/60 bg-cyan-950/20 text-cyan-100' : 'border-borderSoft/60 bg-panelSoft/40 text-slate-300 hover:border-slate-500'}`}
                        onClick={(event) => {
                          event.stopPropagation();
                          onHighlight(highlighted ? undefined : item.id);
                        }}
                      >
                        <p className="text-xs">{item.title}</p>
                        <p className="mt-0.5 text-[10px] uppercase tracking-wide text-slate-500">{item.timeLabel}</p>
                      </button>
                      {highlighted && (
                        <div className="mt-1 rounded-md border border-borderSoft/60 bg-black/20 px-2 py-1 text-xs text-slate-300">
                          <p>{item.detail}</p>
                          <div className="mt-2 flex flex-wrap gap-1">
                            {item.kind === 'reminder' && (
                              <button
                                className="rounded border border-emerald-600/40 px-2 py-0.5 text-[10px] text-emerald-200"
                                onClick={(event) => {
                                  event.stopPropagation();
                                  actions.onMarkReminderDone(item.id);
                                }}
                              >
                                mark done
                              </button>
                            )}
                            {item.kind === 'approval' && (
                              <>
                                <button
                                  className="rounded border border-emerald-600/40 px-2 py-0.5 text-[10px] text-emerald-200"
                                  onClick={(event) => {
                                    event.stopPropagation();
                                    actions.onApprove(item.id);
                                  }}
                                >
                                  approve
                                </button>
                                <button
                                  className="rounded border border-rose-600/40 px-2 py-0.5 text-[10px] text-rose-200"
                                  onClick={(event) => {
                                    event.stopPropagation();
                                    actions.onDeny(item.id);
                                  }}
                                >
                                  deny
                                </button>
                              </>
                            )}
                            {item.kind === 'alert' && (
                              <button
                                className="rounded border border-cyan-600/40 px-2 py-0.5 text-[10px] text-cyan-200"
                                onClick={(event) => {
                                  event.stopPropagation();
                                  actions.onAcknowledgeAlert(item.id);
                                }}
                              >
                                acknowledge
                              </button>
                            )}
                          </div>
                        </div>
                      )}
                    </li>
                  );
                })}
                {visibleItems.length === 0 && <li className="text-xs text-slate-500">No items.</li>}
              </ul>
            </section>
          );
        })}
      </div>
    </aside>
  );
}
