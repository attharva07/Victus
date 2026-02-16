import { useEffect, useState } from 'react';

const primaryStatuses = [
  ['Mode', 'adaptive'],
  ['Planner', 'listening'],
  ['Executor', 'ready'],
  ['Domain', 'automation']
];

const debugStatuses = [
  ['Victus', 'adaptive'],
  ['Lane Engine', 'deterministic'],
  ['Signal Loop', 'realtime']
];

export default function BottomStatusStrip({ confidence, onSimulate }: { confidence: string; onSimulate: () => void }) {
  const [showDebug, setShowDebug] = useState(false);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === '`') setShowDebug((previous) => !previous);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  return (
    <footer data-testid="bottom-status-strip" className="fixed bottom-0 left-0 right-0 z-30 border-t border-borderSoft/70 bg-bg/95 px-6 py-2 text-[11px] text-slate-500 backdrop-blur">
      <div className="mx-auto flex w-full max-w-[1500px] items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-x-5 gap-y-1">
          {primaryStatuses.map(([label, value]) => (
            <p key={label}>
              <span className="uppercase tracking-wide text-slate-600">{label}</span>: <span>{value}</span>
            </p>
          ))}
          <p>
            <span className="uppercase tracking-wide text-slate-600">Confidence</span>: <span>{confidence}</span>
          </p>
          {showDebug &&
            debugStatuses.map(([label, value]) => (
              <p key={label}>
                <span className="uppercase tracking-wide text-slate-600">{label}</span>: <span>{value}</span>
              </p>
            ))}
        </div>

        <button
          className="rounded border border-borderSoft/80 px-2 py-1 text-[10px] lowercase tracking-wide text-slate-300 hover:border-cyan-500/40"
          onClick={onSimulate}
        >
          simulate update
        </button>
      </div>
    </footer>
  );
}
