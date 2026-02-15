import BottomStrip from './components/BottomStrip';
import CommandDock from './components/CommandDock';
import ContextStack from './components/ContextStack';
import LeftRail from './components/LeftRail';
import SystemOverviewCard from './components/SystemOverviewCard';

function App() {
  return (
    <div className="h-screen overflow-hidden bg-bg text-slate-200">
      <div className="grid h-full grid-cols-[64px_minmax(0,1fr)_320px]">
        <LeftRail />

        <main className="relative overflow-y-auto px-6 pb-24 pt-5">
          <div className="mx-auto max-w-4xl pb-24">
            <SystemOverviewCard />
          </div>
          <CommandDock />
        </main>

        <div className="border-l border-borderSoft/70 bg-panel/40 p-3">
          <ContextStack />
        </div>
      </div>
      <BottomStrip />
    </div>
  );
}

export default App;
