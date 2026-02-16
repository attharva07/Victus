import { useState } from 'react';

export default function CommandDock({
  onSubmit,
  onInteract,
  onTypingChange
}: {
  onSubmit: (value: string) => void;
  onInteract: () => void;
  onTypingChange: (typing: boolean) => void;
}) {
  const [value, setValue] = useState('');
  const [expanded, setExpanded] = useState(false);

  return (
    <div data-testid="command-dock-shell" className="pointer-events-none fixed bottom-10 left-1/2 z-40 w-full -translate-x-1/2 px-4">
      <div
        className={`pointer-events-auto mx-auto rounded-xl border border-borderSoft bg-panelSoft/95 transition-all ${expanded ? 'w-full max-w-xl p-3' : 'w-72 p-2'}`}
        onClick={() => {
          setExpanded(true);
          onInteract();
        }}
      >
        <input
          aria-label="Command dock"
          value={value}
          onFocus={() => {
            setExpanded(true);
            onInteract();
          }}
          onBlur={() => onTypingChange(false)}
          onKeyDown={(event) => {
            if (event.key === 'Enter' && value.trim()) {
              onSubmit(value);
              setValue('');
              onTypingChange(false);
              onInteract();
            }
          }}
          onChange={(event) => {
            const next = event.target.value;
            setValue(next);
            onTypingChange(next.trim().length > 0);
            if (next.length > 0) {
              setExpanded(true);
              onInteract();
            }
          }}
          placeholder="Issue a command…"
          className="w-full border-0 bg-transparent text-sm text-slate-100 outline-none placeholder:text-slate-500"
        />
      </div>
    </div>
  );
}
