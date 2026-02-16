import BottomStatusStrip from './components/BottomStrip';
import CommandDock from './components/CommandDock';
import ContextLane from './components/Lanes/ContextLane';
import FocusLane from './components/Lanes/FocusLane';
import LeftRail from './components/LeftRail';
import { AlertsWidget, ApprovalsWidget, FailuresWidget, RemindersWidget, WorkflowsWidget } from './components/widgets/ContextWidgets';
import {
  ApprovalsPanelWidget,
  DialogueWidget,
  HealthPulseWidget,
  RemindersPanelWidget,
  SystemOverviewWidget,
  TimelineWidget,
  WorkflowsBoardWidget,
  WorldTldrWidget
} from './components/widgets/FocusWidgets';
import type { WidgetId } from './layout/types';
import { useLayoutEngine } from './layout/useLayoutEngine';
import { useVictusStore, VictusStoreProvider } from './state/store';
import CameraScreen from './views/CameraScreen';
import FilesScreen from './views/FilesScreen';
import FinanceScreen from './views/FinanceScreen';
import MemoriesScreen from './views/MemoriesScreen';

function AppContent() {
  const { state, actions } = useVictusStore();
  const { plan, pinWidget, pinnedWidgets, resetLayout } = useLayoutEngine(state.data);

  if (!state.data) return <div className="h-screen bg-bg text-slate-200 p-4">Loading Victus UI state…</div>;

  const data = state.data;

  const renderFocusWidget = (id: WidgetId) => {
    const pinned = pinnedWidgets.includes(id);
    if (id === 'dialogue') return <DialogueWidget messages={data.dialogue.messages} pinned={pinned} onTogglePin={() => pinWidget(id)} />;
    if (id === 'timeline') return <TimelineWidget events={[...data.timeline.today, ...data.timeline.upcoming, ...data.timeline.completed]} pinned={pinned} onTogglePin={() => pinWidget(id)} />;
    if (id === 'healthPulse') return <HealthPulseWidget failures={data.contextGroups.failures} pinned={pinned} onTogglePin={() => pinWidget(id)} />;
    if (id === 'systemOverview') return <SystemOverviewWidget reminders={data.contextGroups.reminders.length} approvals={data.contextGroups.approvals.length} failures={data.contextGroups.failures.length} workflows={data.contextGroups.workflows.length} pinned={pinned} onTogglePin={() => pinWidget(id)} />;
    if (id === 'worldTldr') return <WorldTldrWidget items={data.worldTldr} pinned={pinned} onTogglePin={() => pinWidget(id)} />;
    if (id === 'workflowsBoard') return <WorkflowsBoardWidget items={data.contextGroups.workflows} onResume={actions.resumeWorkflow} pinned={pinned} onTogglePin={() => pinWidget(id)} />;
    if (id === 'remindersPanel') return <RemindersPanelWidget items={data.contextGroups.reminders} onDone={actions.markReminderDone} pinned={pinned} onTogglePin={() => pinWidget(id)} />;
    if (id === 'approvalsPanel') return <ApprovalsPanelWidget items={data.contextGroups.approvals} onApprove={(approvalId) => actions.decideApproval(approvalId, 'approved')} onDeny={(approvalId) => actions.decideApproval(approvalId, 'denied')} pinned={pinned} onTogglePin={() => pinWidget(id)} />;
    return null;
  };

  const renderContextWidget = (id: WidgetId) => {
    if (id === 'failures') return <FailuresWidget items={data.contextGroups.failures} />;
    if (id === 'approvals') return <ApprovalsWidget items={data.contextGroups.approvals} onApprove={(approvalId) => actions.decideApproval(approvalId, 'approved')} onDeny={(approvalId) => actions.decideApproval(approvalId, 'denied')} />;
    if (id === 'alerts') return <AlertsWidget items={data.contextGroups.alerts} onAck={actions.ackAlert} />;
    if (id === 'reminders') return <RemindersWidget items={data.contextGroups.reminders} onDone={actions.markReminderDone} />;
    if (id === 'workflows') return <WorkflowsWidget items={data.contextGroups.workflows} onResume={actions.resumeWorkflow} />;
    return null;
  };

  return (
    <div className="h-screen overflow-hidden bg-bg text-slate-200">
      <div className="grid h-full min-h-0 grid-cols-[64px_minmax(0,1fr)] gap-4 px-3 pb-28 pt-3">
        <LeftRail activeView={state.activeView} onChangeView={actions.setActiveView} />
        <main className="h-full min-h-0 overflow-hidden pb-20">
          {state.activeView === 'overview' ? (
            <div className="grid h-full min-h-0 grid-cols-[minmax(0,1fr)_320px] gap-4">
              <FocusLane placements={plan.focusPlacements} renderWidget={renderFocusWidget} onReset={resetLayout} showReset={false} />
              <ContextLane orderedIds={plan.contextOrder} renderWidget={renderContextWidget} />
            </div>
          ) : null}
          {state.activeView === 'memories' ? <MemoriesScreen /> : null}
          {state.activeView === 'finance' ? <FinanceScreen /> : null}
          {state.activeView === 'files' ? <FilesScreen /> : null}
          {state.activeView === 'camera' ? <CameraScreen /> : null}
        </main>
      </div>

      <CommandDock
        alignToDialogue={true}
        onInteract={() => undefined}
        onTypingChange={actions.setTyping}
        onSubmit={async (text) => {
          await actions.submitCommand(text);
          actions.setActiveView('overview');
        }}
      />
      <BottomStatusStrip
        mode={data.bottomStrip.mode}
        planner={data.bottomStrip.planner}
        executor={data.bottomStrip.executor}
        domain={data.bottomStrip.domain}
        confidence={`stable (${data.bottomStrip.confidence})`}
        onSimulate={() => {
          const first = data.contextGroups.reminders[0];
          if (first) void actions.markReminderDone(first.id);
        }}
      />
    </div>
  );
}

export default function App() {
  return (
    <VictusStoreProvider>
      <AppContent />
    </VictusStoreProvider>
  );
}
