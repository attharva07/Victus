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
import defaultLayoutPlan from './layout/presets';
import {
  addCommandEvent,
  initialVictusState,
  type VictusState
} from './data/victusStore';

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

  const renderView = () => {
    if (activeView === 'overview') {
      return (
        <CardStack
          today={timeline.today}
          upcoming={timeline.upcoming}
          completed={timeline.completed}
          selectedId={selectedId ?? undefined}
          onSelect={setSelectedId}
        />
      );
    }

    if (activeView === 'memories') return <MemoriesScreen />;
    if (activeView === 'finance') return <FinanceScreen />;
    if (activeView === 'files') return <FilesScreen />;
    return <CameraScreen />;
  };

  return (
    <div className="h-screen overflow-hidden bg-bg text-slate-200">
      <div className="grid h-full grid-cols-[64px_minmax(0,1fr)_320px] gap-4 px-3 pb-28 pt-3">
        <LeftRail activeView={activeView} onChangeView={(view) => setActiveView(view)} />

        <main className="h-full overflow-hidden">
          {renderView()}
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
