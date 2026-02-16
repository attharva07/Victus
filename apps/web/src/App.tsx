import { useEffect, useMemo, useState } from 'react';
import BottomStrip from './components/BottomStrip';
import CommandDock from './components/CommandDock';
import ContextStack from './components/ContextStack';
import DetailDrawer from './components/DetailDrawer';
import LeftRail, { type VictusView } from './components/LeftRail';
import SystemOverviewCard from './components/SystemOverviewCard';
import {
  acknowledge,
  addCommandEvent,
  approve,
  deny,
  dismiss,
  initialVictusState,
  markDone,
  mute,
  pinToReminders,
  resolveFailure,
  snooze,
  toggleCard,
  toggleWorkflow,
  type VictusItem,
  type VictusState
} from './data/victusStore';

function PlaceholderView({ title }: { title: string }) {
  return (
    <div className="rounded-xl border border-borderSoft/80 bg-panel p-6">
      <h2 className="text-lg font-medium text-slate-100">{title}</h2>
      <p className="mt-3 text-sm text-slate-400">Coming soon — interactive modules for this domain are being prepared.</p>
    </div>
  );
}

function App() {
  const [state, setState] = useState<VictusState>(initialVictusState);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [activeView, setActiveView] = useState<VictusView>('overview');

  const selectedItem = selectedId ? state.items[selectedId] : undefined;

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

  const applyAndClose = (next: VictusState, id: string) => {
    setState(next);
    if (!next.items[id] || next.items[id].status === 'dismissed') {
      setSelectedId(null);
    }
  };

  const drawerActions = (item: VictusItem) => {
    switch (item.kind) {
      case 'event':
        return item.type === 'user'
          ? [
              { label: 'Mark Done', onClick: () => applyAndClose(markDone(state, item.id), item.id) },
              { label: 'Pin to Reminders', onClick: () => applyAndClose(pinToReminders(state, item.id), item.id) }
            ]
          : [
              { label: 'Acknowledge', onClick: () => applyAndClose(acknowledge(state, item.id), item.id) },
              { label: 'Dismiss', onClick: () => applyAndClose(dismiss(state, item.id), item.id) }
            ];
      case 'reminder':
        return [
          { label: 'Snooze', onClick: () => applyAndClose(snooze(state, item.id), item.id) },
          { label: 'Mark Done', onClick: () => applyAndClose(markDone(state, item.id), item.id) }
        ];
      case 'alert':
        return [
          { label: 'Acknowledge', onClick: () => applyAndClose(acknowledge(state, item.id), item.id) },
          { label: 'Mute', onClick: () => applyAndClose(mute(state, item.id), item.id) }
        ];
      case 'approval':
        return [
          { label: 'Approve', onClick: () => applyAndClose(approve(state, item.id), item.id) },
          { label: 'Deny', onClick: () => applyAndClose(deny(state, item.id), item.id) }
        ];
      case 'workflow':
        return [
          { label: 'View Steps', onClick: () => applyAndClose(acknowledge(state, item.id), item.id) },
          {
            label: item.workflowState === 'paused' ? 'Resume' : 'Pause',
            onClick: () => applyAndClose(toggleWorkflow(state, item.id), item.id)
          }
        ];
      case 'failure':
        return [
          { label: 'Open Logs', onClick: () => applyAndClose(acknowledge(state, item.id), item.id) },
          { label: 'Retry', onClick: () => applyAndClose(acknowledge(state, item.id), item.id) },
          { label: 'Mark Resolved', onClick: () => applyAndClose(resolveFailure(state, item.id), item.id) }
        ];
      default:
        return [];
    }
  };

  return (
    <div className="h-screen overflow-hidden bg-bg text-slate-200">
      <div className="grid h-full grid-cols-[64px_minmax(0,1fr)_320px]">
        <LeftRail activeView={activeView} onChangeView={(view) => setActiveView(view)} />

        <main className="subtle-scrollbar relative overflow-y-auto px-6 pb-24 pt-5">
          <div className="mx-auto max-w-4xl pb-24">
            {activeView === 'overview' ? (
              <SystemOverviewCard
                today={timeline.today}
                upcoming={timeline.upcoming}
                completed={timeline.completed}
                selectedId={selectedId ?? undefined}
                onSelect={setSelectedId}
              />
            ) : (
              <PlaceholderView title={activeView.charAt(0).toUpperCase() + activeView.slice(1)} />
            )}
          </div>
          <CommandDock onSubmit={(text) => setState((prev) => addCommandEvent(prev, text))} />
        </main>

        <div className="border-l border-borderSoft/70 bg-panel/40 p-3">
          {activeView === 'overview' && selectedItem ? (
            <DetailDrawer item={selectedItem} actions={drawerActions(selectedItem)} onClose={() => setSelectedId(null)} />
          ) : (
            <ContextStack
              cards={state.contextCards}
              items={state.items}
              selectedId={selectedId ?? undefined}
              onToggleCard={(kind) => setState((prev) => toggleCard(prev, kind))}
              onSelect={setSelectedId}
            />
          )}
        </div>
      </div>
      <BottomStrip />
    </div>
  );
}

export default App;
