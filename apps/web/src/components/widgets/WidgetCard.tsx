import { useEffect, useRef, useState, type ReactNode } from 'react';

export default function WidgetCard({
  title,
  children,
  canExpand,
  pinned,
  onTogglePin,
  testId,
  defaultExpanded = false
}: {
  title: string;
  children: ReactNode;
  canExpand: boolean;
  pinned?: boolean;
  onTogglePin?: () => void;
  testId: string;
  defaultExpanded?: boolean;
}) {
  const [expanded, setExpanded] = useState(defaultExpanded);
  const [showExpand, setShowExpand] = useState(canExpand);
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!canExpand) {
      setShowExpand(false);
      return;
    }

    const node = contentRef.current;
    if (!node) return;

    const checkOverflow = () => {
      setShowExpand(canExpand || node.scrollHeight > node.clientHeight + 4);
    };

    checkOverflow();
    const raf = window.requestAnimationFrame(checkOverflow);
    window.addEventListener('resize', checkOverflow);
    return () => {
      window.cancelAnimationFrame(raf);
      window.removeEventListener('resize', checkOverflow);
    };
  }, [children, canExpand, expanded]);

  const togglable = showExpand;

  return (
    <article data-testid={testId} data-expanded={expanded ? 'true' : 'false'} className="rounded-xl border border-borderSoft/70 bg-panel/80 p-3 transition">
      <header
        data-testid={`${testId}-header`}
        className={`mb-2 flex items-center justify-between ${togglable ? 'cursor-pointer' : ''}`}
        onClick={() => togglable && setExpanded((previous) => !previous)}
      >
        <h3 className="text-sm text-slate-100">{title}</h3>
        <div className="flex items-center gap-2">
          {onTogglePin && (
            <button
              type="button"
              aria-label={`pin-${title}`}
              className={`rounded border px-1.5 py-0.5 text-[10px] ${pinned ? 'border-cyan-500/50 text-cyan-200' : 'border-borderSoft text-slate-400'}`}
              onClick={(event) => {
                event.stopPropagation();
                onTogglePin();
              }}
            >
              pin
            </button>
          )}
          {togglable ? <span className="text-[10px] text-slate-500">{expanded ? 'collapse' : 'expand'}</span> : null}
        </div>
      </header>

      <div
        ref={contentRef}
        data-testid={`${testId}-body`}
        className={`${expanded ? 'max-h-[420px] overflow-y-auto' : 'max-h-28 overflow-hidden'} transition-all duration-200`}
        onClick={() => togglable && setExpanded((previous) => !previous)}
      >
        {children}
      </div>
    </article>
  );
}
