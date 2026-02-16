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
  const [resolvingIds, setResolvingIds] = useState<Set<string>>(new Set());
  const [feedback, setFeedback] = useState<string | null>(null);

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

  const handleApprovalResolution = (item: VictusItem, decision: 'approved' | 'denied') => {
    setResolvingIds((previous) => new Set(previous).add(item.id));

    window.setTimeout(() => {
      if (decision === 'approved') {
        actions.onApprove(item.id);
      } else {
        actions.onDeny(item.id);
      }
      onHighlight(undefined);
      setResolvingIds((previous) => {
        const next = new Set(previous);
        next.delete(item.id);
        return next;
      });
      setFeedback(`Approval resolved (${decision})`);
      window.setTimeout(() => setFeedback(null), 1600);
    }, 220);
  };

  return (
    <aside className="h-full overflow-hidden rounded-2xl border border-borderSoft/60 bg-panel/30 p-3">
      <section data-testid="context-stack-container" className="flex h-full flex-col rounded-xl border border-borderSoft/70 bg-panel/80 px-3 py-2">
        <header className="mb-2 flex items-center justify-between">
          <h2 className="text-xs uppercase tracking-[0.15em] text-slate-300">Context Stack</h2>
          <div className="flex items-center gap-2">
            {feedback && <span className="rounded-full border border-emerald-600/30 px-2 py-0.5 text-[10px] text-emerald-200">{feedback}</span>}
            <span className="text-[10px] text-slate-500">{visibleSections.length} sections</span>
          </div>
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

                <div
                  className={`grid overflow-hidden transition-all duration-300 ease-out ${isExpanded ? 'mt-2 grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'}`}
                >
                  <ul className="min-h-0 space-y-2">
                    {cardItems.map((item) => {
                      const highlighted = highlightedId === item.id;
                      const isResolving = resolvingIds.has(item.id);

                      return (
                        <li
                          key={item.id}
                          className={`overflow-hidden transition-all duration-200 ${isResolving ? 'max-h-0 opacity-0' : 'max-h-48 opacity-100'}`}
                        >
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

                          {item.kind === 'approval' && (
                            <div className="mt-1 flex gap-1">
                              <button
                                className="rounded border border-emerald-600/40 px-2 py-0.5 text-[10px] text-emerald-200"
                                onClick={(event) => {
                                  event.stopPropagation();
                                  handleApprovalResolution(item, 'approved');
                                }}
                              >
                                Approve
                              </button>
                              <button
                                className="rounded border border-rose-600/40 px-2 py-0.5 text-[10px] text-rose-200"
                                onClick={(event) => {
                                  event.stopPropagation();
                                  handleApprovalResolution(item, 'denied');
                                }}
                              >
                                Deny
                              </button>
                            </div>
                          )}

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
                </div>
              </section>
            );
          })}
        </div>
      </section>
    </aside>
  );
}
