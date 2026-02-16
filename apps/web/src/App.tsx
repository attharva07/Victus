import { useState } from 'react';
import BottomStatusStrip from './components/BottomStrip';
import CommandDock from './components/CommandDock';
import ContextLane from './components/Lanes/ContextLane';
import FocusLane from './components/Lanes/FocusLane';
import LeftRail, { type VictusView } from './components/LeftRail';
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
import { applyApprovalDecision, initialMockState, markReminderDone, submitCommand, type MockUiState } from './state/mockState';
import CameraScreen from './views/CameraScreen';
import FilesScreen from './views/FilesScreen';
import FinanceScreen from './views/FinanceScreen';
import MemoriesScreen from './views/MemoriesScreen';

function App() {
  const [activeView, setActiveView] = useState<VictusView>('overview');
  const [state, setState] = useState<MockUiState>(initialMockState);
  const { plan, pinWidget, pinnedWidgets, resetLayout } = useLayoutEngine(state);

  const approve = (id: string, decision: 'approved' | 'denied') => setState((prev) => applyApprovalDecision(prev, id, decision));
  const markDone = (id: string) => setState((prev) => markReminderDone(prev, id));

  const renderFocusWidget = (id: WidgetId) => {
    const pinned = pinnedWidgets.includes(id);
    if (id === 'dialogue') return <DialogueWidget messages={state.dialogue} pinned={pinned} onTogglePin={() => pinWidget(id)} />;
    if (id === 'timeline') return <TimelineWidget events={state.timeline} pinned={pinned} onTogglePin={() => pinWidget(id)} />;
    if (id === 'healthPulse') return <HealthPulseWidget failures={state.failures} pinned={pinned} onTogglePin={() => pinWidget(id)} />;
    if (id === 'systemOverview') return <SystemOverviewWidget reminders={state.reminders.length} approvals={state.approvals.length} failures={state.failures.length} workflows={state.workflows.length} pinned={pinned} onTogglePin={() => pinWidget(id)} />;
    if (id === 'worldTldr') return <WorldTldrWidget items={state.worldTldr} pinned={pinned} onTogglePin={() => pinWidget(id)} />;
    if (id === 'workflowsBoard') return <WorkflowsBoardWidget items={state.workflows} pinned={pinned} onTogglePin={() => pinWidget(id)} />;
    if (id === 'remindersPanel') return <RemindersPanelWidget items={state.reminders} onDone={markDone} pinned={pinned} onTogglePin={() => pinWidget(id)} />;
    if (id === 'approvalsPanel') return <ApprovalsPanelWidget items={state.approvals} onApprove={(approvalId) => approve(approvalId, 'approved')} onDeny={(approvalId) => approve(approvalId, 'denied')} pinned={pinned} onTogglePin={() => pinWidget(id)} />;
    return null;
  };

  const renderContextWidget = (id: WidgetId) => {
    if (id === 'failures') return <FailuresWidget items={state.failures} />;
    if (id === 'approvals') return <ApprovalsWidget items={state.approvals} onApprove={(approvalId) => approve(approvalId, 'approved')} onDeny={(approvalId) => approve(approvalId, 'denied')} />;
    if (id === 'alerts') return <AlertsWidget items={state.alerts} />;
    if (id === 'reminders') return <RemindersWidget items={state.reminders} />;
    if (id === 'workflows') return <WorkflowsWidget items={state.workflows} />;
    return null;
  };

  return (
    <div className="h-screen overflow-hidden bg-bg text-slate-200">
      <div className="grid h-full min-h-0 grid-cols-[64px_minmax(0,1fr)] gap-4 px-3 pb-28 pt-3">
        <LeftRail activeView={activeView} onChangeView={(view) => setActiveView(view)} />
        <main className="h-full min-h-0 overflow-hidden pb-20">
          {activeView === 'overview' ? (
            <div className="grid h-full min-h-0 grid-cols-[minmax(0,1fr)_320px] gap-4">
              <FocusLane placements={plan.focusPlacements} renderWidget={renderFocusWidget} onReset={resetLayout} showReset={false} />
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
        alignToDialogue={true}
        onInteract={() => undefined}
        onTypingChange={() => undefined}
        onSubmit={(text) => {
          setState((prev) => submitCommand(prev, text));
          setActiveView('overview');
        }}
      />
      <BottomStatusStrip confidence={`stable (${state.confidence})`} onSimulate={() => setState((prev) => prev.reminders[0] ? markReminderDone(prev, prev.reminders[0].id) : prev)} />
    </div>
  );
}

export default App;
