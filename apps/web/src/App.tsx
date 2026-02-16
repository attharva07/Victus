import { useEffect, useMemo, useState } from 'react';
import BottomStrip from './components/BottomStrip';
import CardStack from './components/CardStack';
import CommandDock from './components/CommandDock';
import LeftRail, { type VictusView } from './components/LeftRail';
import RightStack from './components/RightStack';
import defaultLayoutPlan from './layout/presets';
import {
  addCommandEvent,
  initialVictusState,
  type VictusState
} from './data/victusStore';

function PlaceholderView({ title }: { title: string }) {
  return (
    <div className="flex h-full items-center justify-center rounded-xl border border-borderSoft/80 bg-panel">
      <div>
        <h2 className="text-lg font-medium text-slate-100">{title}</h2>
        <p className="mt-2 text-sm text-slate-400">Command surface for this domain is being prepared.</p>
      </div>
    </div>
  );
}

function App() {
  const [state, setState] = useState<VictusState>(initialVictusState);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [activeView, setActiveView] = useState<VictusView>('overview');

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

  return (
    <div className="h-screen overflow-hidden bg-bg text-slate-200">
      <div className="grid h-full grid-cols-[64px_minmax(0,1fr)_320px] gap-4 px-3 pb-28 pt-3">
        <LeftRail activeView={activeView} onChangeView={(view) => setActiveView(view)} />

        <main className="h-full overflow-hidden">
          {activeView === 'overview' ? (
            <CardStack
              today={timeline.today}
              upcoming={timeline.upcoming}
              completed={timeline.completed}
              selectedId={selectedId ?? undefined}
              onSelect={setSelectedId}
            />
          ) : (
            <PlaceholderView title={activeView.charAt(0).toUpperCase() + activeView.slice(1)} />
          )}
        </main>

        <section className="h-full overflow-hidden">
          <RightStack cards={state.contextCards} items={state.items} selectedId={selectedId ?? undefined} onSelect={setSelectedId} />
        </section>
      </div>

      <CommandDock onSubmit={(text) => setState((prev) => addCommandEvent(prev, text))} />
      <BottomStrip />

      <div className="sr-only" aria-live="polite">
        Active preset: {defaultLayoutPlan.preset}
      </div>
    </div>
  );
}

export default App;
