import { useMemo, useState } from 'react';
import BottomStatusStrip from './components/BottomStrip';
import CenterFocusLane from './components/CenterFocusLane';
import CommandDock from './components/CommandDock';
import LeftRail, { type VictusView } from './components/LeftRail';
import RightContextLane from './components/RightContextLane';
import CameraScreen from './views/CameraScreen';
import FilesScreen from './views/FilesScreen';
import FinanceScreen from './views/FinanceScreen';
import MemoriesScreen from './views/MemoriesScreen';
import {
  acknowledge,
  approve,
  deny,
  initialVictusState,
  markDone,
  type VictusState,
  type VictusItem
} from './data/victusStore';
import { generateLayoutPlan } from './layout/engine';
import { getInitialSignals, simulateUpdate } from './layout/mockSignals';
import type { LayoutSignals } from './layout/signals';

type DialogueMessage = {
  id: string;
  role: 'user' | 'system';
  text: string;
};

const dialogueSeed: DialogueMessage[] = [
  { id: 'd1', role: 'system', text: 'Victus is active. Issue a command when ready.' },
  { id: 'd2', role: 'user', text: 'Bring urgent work to the top.' }
];

function deriveSeverity(count: number): LayoutSignals['failuresSeverity'] {
  if (count >= 3) return 'critical';
  if (count >= 2) return 'high';
  if (count === 1) return 'medium';
  return 'none';
}

function deriveAlertSeverity(alerts: VictusItem[]): LayoutSignals['alertsSeverity'] {
  const pending = alerts.filter((item) => !item.acknowledged);
  if (pending.length >= 3) return 'high';
  if (pending.length >= 2) return 'medium';
  if (pending.length === 1) return 'low';
  return 'none';
}

function recalculateSignals(state: VictusState, previous: LayoutSignals): LayoutSignals {
  const reminders = state.contextCards
    .find((card) => card.kind === 'reminders')
    ?.itemIds.map((id) => state.items[id])
    .filter(Boolean)
    .filter((item) => item.status === 'active') ?? [];

  const approvals = state.contextCards
    .find((card) => card.kind === 'approvals')
    ?.itemIds.map((id) => state.items[id])
    .filter(Boolean)
    .filter((item) => item.approvalState === 'pending') ?? [];

  const alerts = state.contextCards.find((card) => card.kind === 'alerts')?.itemIds.map((id) => state.items[id]).filter(Boolean) ?? [];
  const failures =
    state.contextCards
      .find((card) => card.kind === 'failures')
      ?.itemIds.map((id) => state.items[id])
      .filter(Boolean)
      .filter((item) => item.status === 'active') ?? [];

  const workflows =
    state.contextCards
      .find((card) => card.kind === 'workflows')
      ?.itemIds.map((id) => state.items[id])
      .filter(Boolean)
      .filter((item) => item.workflowState !== 'paused') ?? [];

  return {
    ...previous,
    remindersCount: reminders.length,
    remindersDueToday: reminders.filter((item) => item.timeLabel.includes('due') || item.timeLabel.includes('left')).length,
    approvalsPending: approvals.length,
    alertsCount: alerts.length,
    alertsSeverity: deriveAlertSeverity(alerts),
    failuresCount: failures.length,
    failuresSeverity: deriveSeverity(failures.length),
    workflowsActive: workflows.length
  };
}

function App() {
  const [state, setState] = useState<VictusState>(initialVictusState);
  const [activeView, setActiveView] = useState<VictusView>('overview');
  const [dialogueMessages, setDialogueMessages] = useState<DialogueMessage[]>(dialogueSeed);
  const [signals, setSignals] = useState<LayoutSignals>(getInitialSignals());
  const [highlightedContextItemId, setHighlightedContextItemId] = useState<string | undefined>();

  const timeline = useMemo(
    () => ({
      today: state.timeline.today.map((id) => state.items[id]).filter(Boolean),
      upcoming: state.timeline.upcoming.map((id) => state.items[id]).filter(Boolean)
    }),
    [state]
  );

  const outcomes = useMemo(
    () => {
      const all = Object.values(state.items);
      return {
        reminders: all.filter((item) => item.kind === 'reminder' && item.status === 'active'),
        approvals: all.filter((item) => item.kind === 'approval'),
        workflows: all.filter((item) => item.kind === 'workflow'),
        failures: all.filter((item) => item.kind === 'failure' && item.status === 'active'),
        alerts: all.filter((item) => item.kind === 'alert')
      };
    },
    [state.items]
  );

  const plan = useMemo(() => generateLayoutPlan(signals), [signals]);

  const onMutateState = (mutator: (current: VictusState) => VictusState) => {
    setState((current) => {
      const next = mutator(current);
      setSignals((previous) => recalculateSignals(next, previous));
      return next;
    });
  };

  const handleCommandSubmit = (text: string) => {
    const clean = text.trim();
    if (!clean) return;

    const stamp = Date.now();
    setDialogueMessages((previous) => [
      ...previous,
      { id: `d-user-${stamp}`, role: 'user', text: clean },
      { id: `d-system-${stamp}`, role: 'system', text: `Command accepted: ${clean}` }
    ]);

    setSignals((previous) => ({
      ...previous,
      dialogueOpen: true,
      userTyping: false
    }));

    setActiveView('overview');
  };

  const simulate = () => {
    setSignals((previous) => simulateUpdate(previous));
    onMutateState((current) => {
      const next = { ...current };
      if (!next.items.f2) {
        next.items = {
          ...next.items,
          f2: {
            id: 'f2',
            kind: 'failure',
            title: 'Replay backlog exceeded',
            detail: 'Failure simulator added backlog pressure.',
            timeLabel: 'just now',
            type: 'system',
            source: 'Simulator',
            domain: 'Automation',
            createdAt: '2026-02-16 10:00',
            updatedAt: '2026-02-16 10:00',
            status: 'active'
          }
        };
        next.contextCards = next.contextCards.map((card) =>
          card.kind === 'failures' ? { ...card, itemIds: ['f2', ...card.itemIds] } : card
        );
      }
      return next;
    });
  };

  return (
    <div className="h-screen overflow-hidden bg-bg text-slate-200">
      <div className="grid h-full grid-cols-[64px_minmax(0,1fr)] gap-4 px-3 pb-24 pt-3">
        <LeftRail activeView={activeView} onChangeView={(view) => setActiveView(view)} />

        <main className="h-full overflow-hidden">
          {activeView === 'overview' ? (
            <div className="grid h-full grid-cols-[minmax(0,1fr)_320px] gap-4">
              <CenterFocusLane
                plan={plan}
                signals={signals}
                today={timeline.today}
                upcoming={timeline.upcoming}
                outcomes={outcomes}
                dialogueMessages={dialogueMessages}
                onToggleCard={() => undefined}
              />
              <RightContextLane
                orderedCardIds={plan.rightContextCardIds}
                cards={state.contextCards}
                items={state.items}
                highlightedId={highlightedContextItemId}
                onHighlight={setHighlightedContextItemId}
                actions={{
                  onMarkReminderDone: (id) => onMutateState((current) => markDone(current, id)),
                  onApprove: (id) => onMutateState((current) => approve(current, id)),
                  onDeny: (id) => onMutateState((current) => deny(current, id)),
                  onAcknowledgeAlert: (id) => onMutateState((current) => acknowledge(current, id))
                }}
              />
            </div>
          ) : null}

          {activeView === 'memories' ? <MemoriesScreen /> : null}
          {activeView === 'finance' ? <FinanceScreen /> : null}
          {activeView === 'files' ? <FilesScreen /> : null}
          {activeView === 'camera' ? <CameraScreen /> : null}
        </main>
      </div>

      <CommandDock
        alignToDialogue={plan.dominantCardId === 'dialogue'}
        onInteract={() => setSignals((previous) => ({ ...previous, dialogueOpen: true }))}
        onTypingChange={(typing) => setSignals((previous) => ({ ...previous, dialogueOpen: true, userTyping: typing }))}
        onSubmit={handleCommandSubmit}
      />
      <BottomStatusStrip confidence={`${signals.confidenceStability} (${signals.confidenceScore})`} onSimulate={simulate} />

      <div className="sr-only" aria-live="polite">
        Active preset: {plan.preset}. Dominant: {plan.dominantCardId}. remindersCount: {signals.remindersCount}.
      </div>
    </div>
  );
}

export default App;
