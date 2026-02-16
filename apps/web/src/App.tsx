import { useMemo, useState } from 'react';
import BottomStatusStrip from './components/BottomStrip';
import CommandDock from './components/CommandDock';
import ContextLane from './components/Lanes/ContextLane';
import FocusLane from './components/Lanes/FocusLane';
import LeftRail, { type VictusView } from './components/LeftRail';
import {
  approve,
  deny,
  initialVictusState,
  markDone,
  type VictusItem,
  type VictusState
} from './data/victusStore';
import { useLayoutEngine } from './layout/useLayoutEngine';
import type { WidgetId, WidgetRuntimeSignals } from './layout/types';
import {
  AlertsWidget,
  ApprovalsWidget,
  FailuresWidget,
  RemindersWidget,
  WorkflowsWidget
} from './components/widgets/ContextWidgets';
import {
  DialogueWidget,
  HealthPulseWidget,
  SystemOverviewWidget,
  TimelineWidget
} from './components/widgets/FocusWidgets';
import MemoriesScreen from './views/MemoriesScreen';
import FinanceScreen from './views/FinanceScreen';
import FilesScreen from './views/FilesScreen';
import CameraScreen from './views/CameraScreen';

type DialogueMessage = { id: string; role: 'user' | 'system'; text: string };

const dialogueSeed: DialogueMessage[] = [
  { id: 'd1', role: 'system', text: 'Victus is active. Issue a command when ready.' }
];

function App() {
  const [state, setState] = useState<VictusState>(initialVictusState);
  const [activeView, setActiveView] = useState<VictusView>('overview');
  const [dialogueMessages, setDialogueMessages] = useState<DialogueMessage[]>(dialogueSeed);
  const [dialogueOpen, setDialogueOpen] = useState(false);

  const today = useMemo(() => state.timeline.today.map((id) => state.items[id]).filter(Boolean), [state]);
  const upcoming = useMemo(() => state.timeline.upcoming.map((id) => state.items[id]).filter(Boolean), [state]);

  const reminders = getContextItems(state, 'reminders').filter((item) => item.status === 'active');
  const alerts = getContextItems(state, 'alerts');
  const approvals = getContextItems(state, 'approvals');
  const workflows = getContextItems(state, 'workflows').filter((item) => item.workflowState !== 'paused');
  const failures = getContextItems(state, 'failures').filter((item) => item.status === 'active');
  const approvalsPendingCount = approvals.filter((item) => item.approvalState === 'pending').length;

  const signals: WidgetRuntimeSignals = useMemo(
    () => ({
      dialogue: { urgency: dialogueOpen ? 92 : 22, confidence: 84 },
      systemOverview: { urgency: 40 + reminders.length * 4 + approvals.length * 5, confidence: 76 },
      timeline: { urgency: 44 + today.length * 2, confidence: 70 },
      healthPulse: { urgency: 35 + failures.length * 18, confidence: 62, failureBoost: failures.length > 0 ? 12 : 0 },
      reminders: { urgency: 48 + reminders.length * 7, confidence: 66 },
      alerts: { urgency: 52 + alerts.length * 6, confidence: 64 },
      approvals: {
        urgency: 58 + approvalsPendingCount * 12,
        confidence: 67,
        approvalBoost: approvals.length > 0 ? 14 : 0
      },
      workflows: { urgency: 34 + workflows.length * 4, confidence: 74 },
      failures: { urgency: 64 + failures.length * 14, confidence: 58, failureBoost: failures.length > 0 ? 16 : 0 }
    }),
    [alerts.length, approvals.length, approvalsPendingCount, dialogueOpen, failures.length, reminders.length, today.length, workflows.length]
  );

  const isDev = import.meta.env.DEV;
  const layoutConfig = useMemo(() => ({ debug: Boolean(import.meta.env.VITE_LAYOUT_DEBUG === '1') }), []);
  const { plan, pinWidget, pinnedWidgets, resetLayout } = useLayoutEngine({
    signals,
    config: layoutConfig,
    devMode: isDev
  });

  const mutate = (updater: (current: VictusState) => VictusState) => setState((current) => updater(current));

  const handleCommandSubmit = (text: string) => {
    const clean = text.trim();
    if (!clean) return;
    const stamp = Date.now();
    setDialogueOpen(true);
    setDialogueMessages((previous) => [
      ...previous,
      { id: `d-user-${stamp}`, role: 'user', text: clean },
      { id: `d-system-${stamp}`, role: 'system', text: 'Queued. Dialogue channel remains active.' }
    ]);
    setActiveView('overview');
  };

  const renderFocusWidget = (id: WidgetId) => {
    if (id === 'dialogue' && !dialogueOpen) return null;
    if (id === 'dialogue') return <DialogueWidget messages={dialogueMessages} pinned={pinnedWidgets.includes(id)} onTogglePin={() => pinWidget(id)} />;
    if (id === 'systemOverview') {
      return (
        <SystemOverviewWidget
          reminders={reminders.length}
          approvals={approvalsPendingCount}
          failures={failures.length}
          workflows={workflows.length}
          pinned={pinnedWidgets.includes(id)}
          onTogglePin={() => pinWidget(id)}
        />
      );
    }
    if (id === 'timeline') return <TimelineWidget today={today} upcoming={upcoming} pinned={pinnedWidgets.includes(id)} onTogglePin={() => pinWidget(id)} />;
    if (id === 'healthPulse') return <HealthPulseWidget failures={failures} pinned={pinnedWidgets.includes(id)} onTogglePin={() => pinWidget(id)} />;
    return null;
  };

  const renderContextWidget = (id: WidgetId) => {
    if (id === 'reminders') return <RemindersWidget items={reminders} />;
    if (id === 'alerts') return <AlertsWidget items={alerts} />;
    if (id === 'approvals') return <ApprovalsWidget items={approvals} onApprove={(itemId) => mutate((current) => approve(current, itemId))} onDeny={(itemId) => mutate((current) => deny(current, itemId))} />;
    if (id === 'workflows') return <WorkflowsWidget items={workflows} />;
    if (id === 'failures') return <FailuresWidget items={failures} />;
    return null;
  };

  return (
    <div className="h-screen overflow-hidden bg-bg text-slate-200">
      <div className="grid h-full min-h-0 grid-cols-[64px_minmax(0,1fr)] gap-4 px-3 pb-24 pt-3">
        <LeftRail activeView={activeView} onChangeView={(view) => setActiveView(view)} />

        <main className="h-full min-h-0 overflow-hidden">
          {activeView === 'overview' ? (
            <div className="grid h-full min-h-0 grid-cols-[minmax(0,1fr)_320px] gap-4">
              <FocusLane placements={plan.focusPlacements.filter((placement) => (placement.id === 'dialogue' ? dialogueOpen : true))} renderWidget={renderFocusWidget} onReset={resetLayout} showReset={isDev} />
              <ContextLane orderedIds={plan.contextOrder} renderWidget={renderContextWidget} />
            </div>
          ) : null}
          {activeView === 'memories' ? <MemoriesScreen /> : null}
          {activeView === 'finance' ? <FinanceScreen /> : null}
          {activeView === 'files' ? <FilesScreen /> : null}
          {activeView === 'camera' ? <CameraScreen /> : null}
        </main>
      </div>

      <CommandDock
        alignToDialogue={dialogueOpen}
        onInteract={() => setDialogueOpen(true)}
        onTypingChange={(typing) => setDialogueOpen((previous) => typing || previous)}
        onSubmit={handleCommandSubmit}
      />
      <BottomStatusStrip confidence={`stable (${Math.round((signals.systemOverview?.confidence ?? 0) + (signals.dialogue?.confidence ?? 0)) / 2})`} onSimulate={() => mutate((current) => markDone(current, current.contextCards[0]?.itemIds[0] ?? ''))} />

      <div className="sr-only" aria-live="polite">
        Layout updated at {new Date(plan.computedAt).toISOString()}
      </div>
    </div>
  );
}

function getContextItems(state: VictusState, kind: VictusState['contextCards'][number]['kind']): VictusItem[] {
  return state.contextCards.find((card) => card.kind === kind)?.itemIds.map((id) => state.items[id]).filter(Boolean) ?? [];
}

export default App;
