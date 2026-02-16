import { useState } from 'react';

export default function CameraScreen() {
  const [captures, setCaptures] = useState<string[]>([]);

  return (
    <section className="h-full rounded-xl border border-borderSoft/80 bg-panel/60 p-3">
      <div className="flex h-full flex-col rounded-lg border border-borderSoft/70 bg-panel p-4">
        <h2 className="text-sm uppercase tracking-[0.14em] text-slate-300">Camera</h2>
        <p className="mt-2 text-sm text-slate-400">Status: standby · mock device connected</p>
        <button
          onClick={() => setCaptures((prev) => [`Capture ${prev.length + 1} @ ${new Date().toLocaleTimeString()}`, ...prev])}
          className="mt-4 w-fit rounded-md border border-cyan-500/50 bg-cyan-500/10 px-3 py-2 text-xs text-cyan-100 hover:bg-cyan-500/20"
        >
          Capture
        </button>

        <ul className="mt-4 min-h-0 flex-1 space-y-2 overflow-y-auto subtle-scrollbar pr-1 text-sm text-slate-300" aria-label="Capture activity">
          {captures.length === 0 ? <li className="text-slate-500">No captures yet.</li> : captures.map((entry) => <li key={entry}>{entry}</li>)}
        </ul>
      </div>
    </section>
  );
}
