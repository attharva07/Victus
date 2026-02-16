const statuses = [
  ['Mode', 'operational'],
  ['Planner', 'adaptive'],
  ['Executor', 'listening'],
  ['Domain', 'system']
];

export default function BottomStrip({ confidence, onSimulate }: { confidence: string; onSimulate: () => void }) {
  return (
    <footer className="fixed bottom-0 left-0 right-0 border-t border-borderSoft/70 bg-bg/95 px-6 py-2 text-[11px] text-slate-500 backdrop-blur">
      <div className="mx-auto flex w-full max-w-[1500px] items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-x-5 gap-y-1">
          {statuses.map(([label, value]) => (
            <p key={label}>
              <span className="uppercase tracking-wide text-slate-600">{label}</span>: <span>{value}</span>
            </p>
          ))}
        </div>

        <div className="flex items-center gap-3">
          <button
            className="rounded border border-borderSoft/80 px-2 py-1 text-[10px] lowercase tracking-wide text-slate-300 hover:border-cyan-500/40"
            onClick={onSimulate}
          >
            simulate update
          </button>
          <p className="text-[10px] lowercase tracking-wide text-slate-600">confidence: {confidence}</p>
        </div>
      </div>
    </footer>
  );
}
