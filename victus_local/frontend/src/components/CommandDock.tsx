import { useState } from 'react';

export default function CommandDock() {
  const [value, setValue] = useState('');
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="pointer-events-none absolute bottom-5 left-1/2 w-full -translate-x-1/2 px-4">
      <div
        className={`pointer-events-auto mx-auto rounded-xl border border-borderSoft bg-panelSoft/95 transition-all ${expanded ? 'w-full max-w-xl p-3' : 'w-72 p-2'}`}
      >
        <input
          aria-label="Command dock"
          value={value}
          onFocus={() => setExpanded(true)}
          onClick={() => setExpanded(true)}
          onChange={(event) => {
            const next = event.target.value;
            setValue(next);
            if (next.length > 0) {
              setExpanded(true);
            }
          }}
          placeholder="Issue a command…"
          className="w-full border-0 bg-transparent text-sm text-slate-100 outline-none placeholder:text-slate-500"
        />
      </div>
    </div>
  );
}
