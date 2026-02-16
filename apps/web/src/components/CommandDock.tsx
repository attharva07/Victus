import { useEffect, useRef, useState } from 'react';

export default function CommandDock({
  onSubmit,
  onInteract,
  onTypingChange
}: {
  alignToDialogue: boolean;
  onSubmit: (value: string) => void;
  onInteract: () => void;
  onTypingChange: (typing: boolean) => void;
}) {
  const [value, setValue] = useState('');
  const [expanded, setExpanded] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const collapseTimerRef = useRef<number | null>(null);
  const clearCollapseTimer = () => {
    if (collapseTimerRef.current !== null) {
      window.clearTimeout(collapseTimerRef.current);
      collapseTimerRef.current = null;
    }
  };

  const openDock = (focusInput = false) => {
    clearCollapseTimer();
    setExpanded(true);
    onInteract();
    if (focusInput) {
      window.requestAnimationFrame(() => inputRef.current?.focus());
    }
  };

  const scheduleCollapse = () => {
    clearCollapseTimer();
    collapseTimerRef.current = window.setTimeout(() => {
      const inputIsFocused = document.activeElement === inputRef.current;
      const hasText = Boolean(inputRef.current?.value.trim());
      if (!hasText || !inputIsFocused) {
        setExpanded(false);
      }
    }, 3000);
  };

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.ctrlKey && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        openDock(true);
      }
    };

    window.addEventListener('keydown', onKeyDown);
    return () => {
      window.removeEventListener('keydown', onKeyDown);
      clearCollapseTimer();
    };
  }, []);

  return (
    <div data-testid="command-dock-shell" className="pointer-events-none fixed inset-x-0 z-40 px-4 bottom-[74px]">
      <div
        data-testid="command-dock-pill"
        data-expanded={expanded ? 'true' : 'false'}
        className={`pointer-events-auto mx-auto border border-borderSoft bg-panelSoft/95 transition-all duration-200 ${expanded ? 'w-full max-w-xl rounded-xl p-3' : 'h-10 w-52 rounded-full p-2'}`}
        onClick={() => openDock(true)}
      >
        <input
          ref={inputRef}
          aria-label="Command dock"
          value={value}
          onFocus={() => {
            openDock();
          }}
          onBlur={() => {
            onTypingChange(false);
            if (!value.trim()) {
              setExpanded(false);
            }
          }}
          onKeyDown={(event) => {
            if (event.key === 'Enter' && value.trim()) {
              event.preventDefault();
              const submitted = value.trim();
              onSubmit(submitted);
              setValue('');
              onTypingChange(false);
              openDock();
              scheduleCollapse();
              return;
            }

            if (event.key === 'Escape') {
              event.preventDefault();
              if (!value.trim()) {
                setExpanded(false);
                inputRef.current?.blur();
                onTypingChange(false);
              } else {
                setValue('');
                onTypingChange(false);
                openDock();
              }
            }
          }}
          onChange={(event) => {
            const next = event.target.value;
            setValue(next);
            onTypingChange(next.trim().length > 0);
            if (next.length > 0) {
              openDock();
            }
          }}
          placeholder="Issue a command…"
          className="w-full border-0 bg-transparent text-sm text-slate-100 outline-none placeholder:text-slate-500"
        />
      </div>
    </div>
  );
}
