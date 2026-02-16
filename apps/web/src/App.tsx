import { useEffect, useMemo, useState } from 'react';
import BottomStrip from './components/BottomStrip';
import CardStack from './components/CardStack';
import CommandDock from './components/CommandDock';
import LeftRail, { type VictusView } from './components/LeftRail';
import RightStack from './components/RightStack';
import CameraScreen from './views/CameraScreen';
import FilesScreen from './views/FilesScreen';
import FinanceScreen from './views/FinanceScreen';
import MemoriesScreen from './views/MemoriesScreen';
import buildAdaptiveLayoutPlan from './layout/engine';
import type { FocusMode, LayoutSignals, Severity } from './layout/signals';
import { initialVictusState, type VictusState } from './data/victusStore';

type DialogueMessage = {
  id: string;
  role: 'user' | 'system';
  text: string;
};

const dialogueSeed: DialogueMessage[] = [
  { id: 'd1', role: 'system', text: 'Dialogue opened. I can help route your command into a workflow.' },
  { id: 'd2', role: 'user', text: 'Show me unresolved approvals and next actions.' }
];

function App() {
  const [state] = useState<VictusState>(initialVictusState);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [activeView, setActiveView] = useState<VictusView>('overview');
  const [dialogueMessages, setDialogueMessages] = useState<DialogueMessage[]>(dialogueSeed);
  const [dialogueOpen, setDialogueOpen] = useState(false);

  useEffect(() => {
    const onEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setSelectedId(null);
      }
    };

    window.addEventListener('keydown', onEscape);
    return () => window.removeEventListener('keydown', onEscape);
  }, []);

  const timeline = useMemo(
    () => ({
      today: state.timeline.today.map((id) => state.items[id]).filter(Boolean),
      upcoming: state.timeline.upcoming.map((id) => state.items[id]).filter(Boolean),
      completed: state.timeline.completed.map((id) => state.items[id]).filter(Boolean)
    }),
    [state]
  );

  const outcomes = useMemo(
    () => {
      const all = Object.values(state.items);
      return {
        reminders: all.filter((item) => item.kind === 'reminder'),
        approvals: all.filter((item) => item.kind === 'approval'),
        workflows: all.filter((item) => item.kind === 'workflow'),
        failures: all.filter((item) => item.kind === 'failure'),
        alerts: all.filter((item) => item.kind === 'alert')
      };
    },
    [state.items]
  );


  const severityForCount = (count: number): Severity => {
    if (count <= 0) return 'none';
    if (count >= 3) return 'high';
    if (count >= 2) return 'medium';
    return 'low';
  };

  const derivedSignals = useMemo<LayoutSignals>(() => {
    const all = Object.values(state.items);
    const remindersCount = all.filter((item) => item.kind === 'reminder' && item.status === 'active').length;
    const alertsCount = all.filter((item) => item.kind === 'alert' && item.status === 'active').length;
    const failuresCount = all.filter((item) => item.kind === 'failure' && item.status !== 'resolved').length;
    const approvalsPending = all.filter((item) => item.kind === 'approval' && item.approvalState === 'pending').length;
    const workflowsActive = all.filter((item) => item.kind === 'workflow' && item.workflowState === 'active').length;

    let confidence: LayoutSignals['confidence'] = 'stable';
    if (alertsCount >= 2) confidence = 'drifting';
    if (failuresCount >= 2) confidence = 'unstable';

    const alertsSeverity = severityForCount(alertsCount);
    const failuresSeverity: Severity = failuresCount >= 2 ? 'critical' : severityForCount(failuresCount);

    let focusMode: FocusMode = 'default';
    if (dialogueOpen) focusMode = 'focus';
    if (approvalsPending > 0 && dialogueOpen) focusMode = 'review';
    if (failuresSeverity === 'critical') focusMode = 'recovery';

    return {
      remindersCount,
      alertsCount,
      alertsSeverity,
      failuresCount,
      failuresSeverity,
      approvalsPending,
      workflowsActive,
      confidence,
      dialogueOpen,
      focusMode,
      updatedAt: Date.now()
    };
  }, [dialogueOpen, state.items]);

  const activeLayoutPlan = useMemo(() => buildAdaptiveLayoutPlan(derivedSignals), [derivedSignals]);

  const gridTemplateColumns =
    activeLayoutPlan.splitColumns === 'centerFocus'
      ? '64px minmax(0,1.35fr) 280px'
      : activeLayoutPlan.splitColumns === 'rightFocus'
        ? '64px minmax(0,1fr) 360px'
        : '64px minmax(0,1fr) 320px';

  const handleCommandDockIntent = () => {
    if (activeView !== 'overview') {
      setActiveView('overview');
    }
    setDialogueOpen(true);
  };

  const handleCommandSubmit = (text: string) => {
    const clean = text.trim();
    if (!clean) return;

    handleCommandDockIntent();
    const stamp = Date.now();
    setDialogueMessages((prev) => [
      ...prev,
      { id: `d-user-${stamp}`, role: 'user', text: clean },
      { id: `d-system-${stamp}`, role: 'system', text: `Acknowledged. Captured "${clean}" for the next workflow step.` }
    ]);
  };

  return (
    <div className="h-screen overflow-hidden bg-bg text-slate-200">
      <div className="grid h-full gap-4 px-3 pb-28 pt-3" style={{ gridTemplateColumns }}>
        <LeftRail activeView={activeView} onChangeView={(view) => setActiveView(view)} />

        <main className="h-full overflow-hidden">
          {renderView()}
        </main>

        <section className="h-full overflow-hidden">
          <RightStack
            cards={state.contextCards}
            items={state.items}
            selectedId={selectedId ?? undefined}
            onSelect={setSelectedId}
            placements={activeLayoutPlan.placements}
            activeCardId={activeLayoutPlan.activeCardId}
          />
        </section>
      </div>

      <CommandDock onInteract={handleCommandDockIntent} onSubmit={handleCommandSubmit} />
      <BottomStrip />

      <div className="sr-only" aria-live="polite">
        Active preset: {activeLayoutPlan.preset}
      </div>
    </div>
  );

  function renderView() {
    if (activeView === 'overview') {
      return (
        <CardStack
          today={timeline.today}
          upcoming={timeline.upcoming}
          outcomes={outcomes}
          dialogueMessages={dialogueMessages}
          dialogueOpen={dialogueOpen}
          selectedId={selectedId ?? undefined}
          onSelect={setSelectedId}
          placements={activeLayoutPlan.placements}
          activeCardId={activeLayoutPlan.activeCardId}
        />
      );
    }

    if (activeView === 'memories') return <MemoriesScreen />;
    if (activeView === 'finance') return <FinanceScreen />;
    if (activeView === 'files') return <FilesScreen />;
    return <CameraScreen />;
  }
}

export default App;
