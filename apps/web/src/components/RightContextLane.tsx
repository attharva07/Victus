import { useMemo, useState } from 'react';
import type { VictusCard, VictusItem } from '../data/victusStore';
import type { VictusCardId } from '../layout/types';

type ContextActionHandlers = {
  onMarkReminderDone: (id: string) => void;
  onApprove: (id: string) => void;
  onDeny: (id: string) => void;
  onAcknowledgeAlert: (id: string) => void;
};

const sectionOrder: VictusCardId[] = ['alerts', 'reminders', 'approvals', 'workflows'];

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
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['alerts']));

  const visibleSections = useMemo(() => {
    const available = sectionOrder.filter((id) => orderedCardIds.includes(id));
    return available
      .map((id) => cards.find((entry) => entry.kind === id))
      .filter((card): card is VictusCard => Boolean(card));
  }, [cards, orderedCardIds]);

  const toggleSection = (id: string) => {
    setExpandedSections((previous) => {
      const next = new Set(previous);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  return (
    <aside className="h-full overflow-hidden rounded-2xl border border-borderSoft/60 bg-panel/30 p-3">
      <section data-testid="context-stack-container" className="flex h-full flex-col rounded-xl border border-borderSoft/70 bg-panel/80 px-3 py-2">
        <header className="mb-2 flex items-center justify-between">
          <h2 className="text-xs uppercase tracking-[0.15em] text-slate-300">Context Stack</h2>
          <span className="text-[10px] text-slate-500">{visibleSections.length} sections</span>
        </header>

        <div data-testid="right-context-scroll" className="thin-scroll flex h-full flex-col gap-2 overflow-y-auto pr-1 pb-24">
          {visibleSections.map((card) => {
            const isExpanded = expandedSections.has(card.kind);
            const cardItems = card.itemIds.map((id) => items[id]).filter(Boolean);
            return (
              <section key={card.kind} data-testid={`context-stack-section-${card.kind}`} className="rounded-lg border border-borderSoft/70 bg-panelSoft/40 px-2 py-2">
                <button className="flex w-full items-center justify-between text-left" onClick={() => toggleSection(card.kind)}>
                  <h3 className="text-xs uppercase tracking-[0.15em] text-slate-300">{titleMap[card.kind]}</h3>
                  <p className="text-[10px] text-slate-500">{cardItems.length}</p>
                </button>

                {isExpanded && (
                  <ul className="mt-2 space-y-2">
                    {cardItems.map((item) => {
                      const highlighted = highlightedId === item.id;
                      return (
                        <li key={item.id}>
                          <button
                            className={`w-full rounded-md border px-2 py-1.5 text-left ${highlighted ? 'border-cyan-500/60 bg-cyan-950/20 text-cyan-100' : 'border-borderSoft/60 bg-panel text-slate-300 hover:border-slate-500'}`}
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
                  </ul>
                )}
              </section>
            );
          })}
        </div>
      </section>
    </aside>
  );
}
