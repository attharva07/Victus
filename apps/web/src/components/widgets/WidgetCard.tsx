import { useEffect, useRef, useState, type MouseEvent, type ReactNode } from 'react';

const INTERACTIVE_SELECTOR = 'button, a, input, textarea, select, [role="button"], [data-no-expand="true"]';

export default function WidgetCard({
  title,
  children,
  canExpand,
  pinned,
  onTogglePin,
  testId,
  defaultExpanded = false,
  scrollBody = true,
  className
}: {
  title: string;
  children: ReactNode;
  canExpand: boolean;
  pinned?: boolean;
  onTogglePin?: () => void;
  testId: string;
  defaultExpanded?: boolean;
  scrollBody?: boolean;
  className?: string;
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

  const handleToggleFromContainer = (event: MouseEvent<HTMLElement>) => {
    if (!togglable) return;
    if ((event.target as HTMLElement).closest(INTERACTIVE_SELECTOR)) return;
    setExpanded((previous) => !previous);
  };

  const bodyClass = expanded
    ? scrollBody
      ? 'max-h-[420px] overflow-y-auto thin-scroll'
      : 'overflow-visible'
    : 'max-h-28 overflow-hidden';

  return (
    <article data-testid={testId} data-expanded={expanded ? 'true' : 'false'} className={`rounded-xl border border-borderSoft/70 bg-panel/80 p-3 transition ${className ?? ''}`}>
      <header
        data-testid={`${testId}-header`}
        className={`mb-2 flex min-h-7 items-center justify-between ${togglable ? 'cursor-pointer' : ''}`}
        onClick={handleToggleFromContainer}
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
          {togglable ? (
            <button
              type="button"
              className="text-[10px] text-slate-500"
              onClick={(event) => {
                event.stopPropagation();
                setExpanded((previous) => !previous);
              }}
            >
              {expanded ? 'collapse' : 'expand'}
            </button>
          ) : null}
        </div>
      </header>

      <div ref={contentRef} data-testid={`${testId}-body`} className={`${bodyClass} transition-all duration-200`} onClick={handleToggleFromContainer}>
        {children}
      </div>
    </article>
  );
}
