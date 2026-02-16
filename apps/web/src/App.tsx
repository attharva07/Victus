import { useEffect, useMemo, useState } from 'react';
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
import { appendDialogueExchange, dialogueSeed, type DialogueMessage } from './data/dialogueStore';
import { appendTimelineEvent, timelineSeed, type TimelineEvent } from './data/timelineStore';
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

const RECENT_DIALOGUE_WINDOW_MINUTES = 5;
const TIMELINE_TICK_MS = 60_000;

function App() {
  const [state, setState] = useState<VictusState>(initialVictusState);
  const [activeView, setActiveView] = useState<VictusView>('overview');
  const [dialogueMessages, setDialogueMessages] = useState<DialogueMessage[]>(dialogueSeed);
  const [timelineEvents, setTimelineEvents] = useState<TimelineEvent[]>(timelineSeed);
  const [dialogueOpen, setDialogueOpen] = useState(false);
  const [timelineTick, setTimelineTick] = useState(0);

  useEffect(() => {
    const timer = window.setInterval(() => setTimelineTick((previous) => previous + 1), TIMELINE_TICK_MS);
    return () => window.clearInterval(timer);
  }, []);

  const reminders = getContextItems(state, 'reminders').filter((item) => item.status === 'active');
  const alerts = getContextItems(state, 'alerts');
  const approvals = getContextItems(state, 'approvals');
  const workflows = getContextItems(state, 'workflows').filter((item) => item.workflowState !== 'paused');
  const failures = getContextItems(state, 'failures').filter((item) => item.status === 'active');
  const approvalsPendingCount = approvals.filter((item) => item.approvalState === 'pending').length;

  const recentCutoff = Date.now() - RECENT_DIALOGUE_WINDOW_MINUTES * 60_000;
  const hasRecentUserMessage = dialogueMessages.some((message) => message.role === 'user' && message.createdAt >= recentCutoff);
  const dialoguePrimary = hasRecentUserMessage || dialogueOpen;
  const newTimelineEventsSinceTick = timelineEvents.filter((event) => event.tick === timelineTick).length;
  const timelinePrimary = newTimelineEventsSinceTick > 0;
  const healthPrimary = failures.length > 0;

  const signals: WidgetRuntimeSignals = useMemo(
    () => ({
      dialogue: { urgency: dialoguePrimary ? 90 : 24, confidence: 84, role: dialoguePrimary ? 'primary' : 'secondary' },
      systemOverview: { urgency: 40 + reminders.length * 4 + approvals.length * 5, confidence: 76, role: 'secondary' },
      timeline: { urgency: timelinePrimary ? 86 : 44, confidence: 70, role: timelinePrimary ? 'primary' : 'secondary' },
      healthPulse: {
        urgency: 35 + failures.length * 18,
        confidence: 62,
        failureBoost: failures.length > 0 ? 12 : 0,
        role: healthPrimary ? 'primary' : 'secondary'
      },
      reminders: { urgency: 48 + reminders.length * 7, confidence: 66, role: 'secondary' },
      alerts: { urgency: 52 + alerts.length * 6, confidence: 64, role: 'secondary' },
      approvals: {
        urgency: 58 + approvalsPendingCount * 12,
        confidence: 67,
        approvalBoost: approvals.length > 0 ? 14 : 0,
        role: 'primary'
      },
      workflows: { urgency: 34 + workflows.length * 4, confidence: 74, role: 'tertiary' },
      failures: { urgency: 64 + failures.length * 14, confidence: 58, failureBoost: failures.length > 0 ? 16 : 0, role: 'primary' }
    }),
    [alerts.length, approvals.length, approvalsPendingCount, dialoguePrimary, failures.length, healthPrimary, reminders.length, timelinePrimary, workflows.length]
  );

  const isDev = import.meta.env.DEV;
  const layoutConfig = useMemo(() => ({ debug: Boolean(import.meta.env.VITE_LAYOUT_DEBUG === '1') }), []);
  const { plan, pinWidget, pinnedWidgets, resetLayout } = useLayoutEngine({
    signals,
    config: layoutConfig,
    devMode: isDev
  });

  const mutate = (updater: (current: VictusState) => VictusState) => setState((current) => updater(current));

  const handleApprovalResolution = (itemId: string, decision: 'approved' | 'denied') => {
    const label = state.items[itemId]?.title ?? itemId;
    mutate((current) => (decision === 'approved' ? approve(current, itemId) : deny(current, itemId)));
    const now = Date.now();
    setTimelineEvents((previous) =>
      appendTimelineEvent(previous, {
        label: `Approval resolved: ${label} (${decision})`,
        detail: `Approval ${decision} in Context Stack.`,
        createdAt: now,
        tick: timelineTick,
        source: 'approvals'
      })
    );
  };

  const handleCommandSubmit = (text: string) => {
    const clean = text.trim();
    if (!clean) return;
    const stamp = Date.now();
    setDialogueOpen(true);
    setDialogueMessages((previous) => appendDialogueExchange(previous, clean, stamp));

    if (looksLikeCommand(clean)) {
      setTimelineEvents((previous) =>
        appendTimelineEvent(previous, {
          label: `Command issued: ${clean}`,
          detail: 'Command dock submission routed to executor queue.',
          createdAt: stamp,
          tick: timelineTick,
          source: 'command'
        })
      );
    }

    setActiveView('overview');
  };

  const renderFocusWidget = (id: WidgetId) => {
    if (id === 'dialogue' && !dialogueOpen && !hasRecentUserMessage) return null;
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
    if (id === 'timeline') return <TimelineWidget events={timelineEvents} pinned={pinnedWidgets.includes(id)} onTogglePin={() => pinWidget(id)} />;
    if (id === 'healthPulse') return <HealthPulseWidget failures={failures} pinned={pinnedWidgets.includes(id)} onTogglePin={() => pinWidget(id)} />;
    return null;
  };

  const renderContextWidget = (id: WidgetId) => {
    if (id === 'reminders') return <RemindersWidget items={reminders} />;
    if (id === 'alerts') return <AlertsWidget items={alerts} />;
    if (id === 'approvals') {
      return <ApprovalsWidget items={approvals} onApprove={(itemId) => handleApprovalResolution(itemId, 'approved')} onDeny={(itemId) => handleApprovalResolution(itemId, 'denied')} />;
    }
    if (id === 'workflows') return <WorkflowsWidget items={workflows} />;
    if (id === 'failures') return <FailuresWidget items={failures} />;
    return null;
  };

  return (
    <div className="h-screen overflow-hidden bg-bg text-slate-200">
      <div className="grid h-full min-h-0 grid-cols-[64px_minmax(0,1fr)] gap-4 px-3 pb-28 pt-3">
        <LeftRail activeView={activeView} onChangeView={(view) => setActiveView(view)} />

        <main className="h-full min-h-0 overflow-hidden pb-24">
          {activeView === 'overview' ? (
            <div className="grid h-full min-h-0 grid-cols-[minmax(0,1fr)_320px] gap-4">
              <FocusLane placements={plan.focusPlacements.filter((placement) => (placement.id === 'dialogue' ? dialogueOpen || hasRecentUserMessage : true))} renderWidget={renderFocusWidget} onReset={resetLayout} showReset={isDev} />
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

function looksLikeCommand(text: string): boolean {
  const normalized = text.trim().toLowerCase();
  if (!normalized) return false;
  return /(run|execute|start|trigger|queue|deploy|sync)/.test(normalized);
}

export default App;
