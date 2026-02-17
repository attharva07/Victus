import { useMemo, useState } from 'react';
import BottomStatusStrip from './components/BottomStrip';
import CommandDock from './components/CommandDock';
import ContextLane from './components/Lanes/ContextLane';
import FocusLane from './components/Lanes/FocusLane';
import LeftRail, { type VictusView } from './components/LeftRail';
import { AlertsWidget, ApprovalsWidget, FailuresWidget, RemindersWidget, WorkflowsWidget } from './components/widgets/ContextWidgets';
import { DialogueWidget, TimelineWidget } from './components/widgets/FocusWidgets';
import type { AdaptiveItem } from './engine/adaptiveScore';
import { useUIState } from './store/uiState';
import CameraScreen from './views/CameraScreen';
import FilesScreen from './views/FilesScreen';
import FinanceScreen from './views/FinanceScreen';
import MemoriesScreen from './views/MemoriesScreen';

function byKind(items: AdaptiveItem[], kind: AdaptiveItem['kind']) {
  return items.filter((item) => item.kind === kind);
}

export default function App() {
  const [activeView, setActiveView] = useState<VictusView>('overview');
  const { items, timelineEvents, dialogueMessages, workflows, layout, pinState, actions } = useUIState();

  const grouped = useMemo(
    () => ({
      failures: byKind(items, 'failure'),
      approvals: byKind(items, 'approval'),
      alerts: byKind(items, 'alert'),
      reminders: byKind(items, 'reminder'),
      workflows: byKind(items, 'workflow'),
      dialogue: byKind(items, 'dialogue')[0]
    }),
    [items]
  );

  const renderContextWidget = (kindId: string) => {
    if (kindId === 'failure') return <FailuresWidget items={grouped.failures.map((i) => ({ id: i.id, title: i.title, severity: i.severity ?? 'info', ageMinutes: 0 }))} />;
    if (kindId === 'approval') return <ApprovalsWidget items={grouped.approvals.map((i) => ({ id: i.id, title: i.title, detail: i.detail, requestedBy: 'Operator' }))} onApprove={(id) => void actions.approve(id)} onDeny={(id) => void actions.deny(id)} />;
    if (kindId === 'alert') return <AlertsWidget items={grouped.alerts.map((i) => ({ id: i.id, title: i.title, detail: i.detail }))} />;
    if (kindId === 'reminder') return <RemindersWidget items={grouped.reminders.map((i) => ({ id: i.id, title: i.title, due: i.detail, urgency: 'high' }))} onDone={(id) => void actions.done(id)} />;
    if (kindId === 'workflow') return <WorkflowsWidget items={grouped.workflows.map((i) => ({ id: i.id, title: i.title, progress: workflows.find((w) => w.id === i.id)?.progress ?? 0, stepLabel: i.detail, resumable: true }))} onResume={(id) => void actions.resume(id)} onPause={(id) => void actions.pause(id)} onAdvanceStep={(id) => void actions.advanceStep(id)} />;
    return null;
  };

  const focusPlacements = layout.focus.map((card, index) => ({
    id: card.item.id,
    score: card.score,
    role: 'secondary' as const,
    sizePreset: card.size === 'FULL' ? 'L' : card.size === 'XL' ? 'L' : card.size,
    heightHint: card.size === 'XL' ? 4 : card.size === 'L' ? 3 : 2,
    column: (index % 2 === 0 ? 'left' : 'right') as 'left' | 'right'
  }));

  const contextOrder = Array.from(new Set(layout.context.map((card) => card.item.kind)));

  const renderFocusWidget = (id: string) => {
    const item = layout.focus.find((card) => card.item.id === id)?.item;
    const pinned = Boolean(pinState[id]);
    if (!item) return null;

    if (item.kind === 'dialogue') {
      return (
        <DialogueWidget
          messages={dialogueMessages.map((message) => ({ id: message.id, role: message.role, text: message.text, createdAt: message.created_at }))}
          pinned={pinned}
          onTogglePin={() => actions.togglePin(item.id)}
        />
      );
    }

    return (
      <div className="transition-all duration-300 ease-out">
        {item.kind === 'failure' ? <FailuresWidget items={[{ id: item.id, title: item.title, severity: item.severity ?? 'critical', ageMinutes: 0 }]} /> : null}
        {item.kind === 'approval' ? <ApprovalsWidget items={[{ id: item.id, title: item.title, detail: item.detail, requestedBy: 'Operator' }]} onApprove={(next) => void actions.approve(next)} onDeny={(next) => void actions.deny(next)} /> : null}
        {item.kind === 'reminder' ? <RemindersWidget items={[{ id: item.id, title: item.title, due: item.detail, urgency: 'high' }]} onDone={(next) => void actions.done(next)} /> : null}
        {item.kind === 'workflow' ? <WorkflowsWidget items={[{ id: item.id, title: item.title, progress: workflows.find((w) => w.id === item.id)?.progress ?? 0, stepLabel: item.detail, resumable: true }]} onResume={(next) => void actions.resume(next)} onPause={(next) => void actions.pause(next)} onAdvanceStep={(next) => void actions.advanceStep(next)} /> : null}
      </div>
    );
  };

  return (
    <div className="h-screen overflow-hidden bg-bg text-slate-200">
      <div className="grid h-full min-h-0 grid-cols-[64px_minmax(0,1fr)] gap-4 px-3 pb-28 pt-3">
        <LeftRail activeView={activeView} onChangeView={setActiveView} />
        <main className="h-full min-h-0 overflow-hidden pb-20">
          {activeView === 'overview' ? (
            <div className="grid h-full min-h-0 grid-cols-[minmax(0,1fr)_320px] gap-4">
              <section className="grid h-full min-h-0 grid-rows-[auto_minmax(0,1fr)] gap-3">
                <TimelineWidget
                  events={timelineEvents.map((event) => ({ ...event, bucket: 'Today' as const }))}
                  pinned={Boolean(pinState['timeline-stream'])}
                  onTogglePin={() => actions.togglePin('timeline-stream')}
                />
                <FocusLane placements={focusPlacements} renderWidget={renderFocusWidget} onReset={() => undefined} showReset={false} />
              </section>
              <ContextLane orderedIds={contextOrder} renderWidget={(kind) => <div className="transition-all duration-300 ease-out">{renderContextWidget(kind)}</div>} />
            </div>
          ) : null}
          {activeView === 'memories' ? <MemoriesScreen /> : null}
          {activeView === 'finance' ? <FinanceScreen /> : null}
          {activeView === 'files' ? <FilesScreen /> : null}
          {activeView === 'camera' ? <CameraScreen /> : null}
        </main>
      </div>

      <CommandDock alignToDialogue={true} onInteract={() => undefined} onTypingChange={() => undefined} onSubmit={(value) => void actions.sendCommand(value)} />
      <BottomStatusStrip mode={'adaptive'} planner={'active'} executor={'ready'} domain={'automation'} confidence={'stable (78)'} onSimulate={() => undefined} />
    </div>
  );
}
