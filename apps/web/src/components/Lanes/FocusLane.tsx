import type { ReactNode } from 'react';
import type { FocusPlacement } from '../../layout/types';

export default function FocusLane({
  placements,
  renderWidget,
  onReset,
  showReset
}: {
  placements: FocusPlacement[];
  renderWidget: (id: FocusPlacement['id']) => ReactNode;
  onReset: () => void;
  showReset: boolean;
}) {
  return (
    <section className="h-full min-h-0 overflow-hidden rounded-2xl border border-borderSoft/60 bg-panel/45 p-3" aria-label="Focus lane">
      <div className="mb-2 flex items-center justify-between">
        <p className="text-xs uppercase tracking-[0.15em] text-slate-500">Focus</p>
        {showReset ? (
          <button className="rounded border border-borderSoft/70 px-2 py-0.5 text-[10px] text-slate-400" onClick={onReset}>Reset layout</button>
        ) : null}
      </div>
      <div data-testid="focus-lane-grid" className="thin-scroll h-full min-h-0 overflow-y-auto pb-32">
        <div className="grid grid-cols-12 gap-3">
          {placements.map((placement) => (
            <div key={placement.id} style={{ gridColumn: `${placement.colStart} / span ${placement.span}` }} data-testid={`focus-placement-${placement.id}`}>
              {renderWidget(placement.id)}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
