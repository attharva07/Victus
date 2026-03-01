import type { ReactNode } from 'react';

export type FocusLanePlacement = {
  id: string;
  score: number;
  role: 'primary' | 'secondary' | 'tertiary';
  sizePreset: 'S' | 'M' | 'L';
  heightHint: number;
  column: 'left' | 'right';
};

export default function FocusLane({
  placements,
  renderWidget,
  onReset,
  showReset
}: {
  placements: FocusLanePlacement[];
  renderWidget: (id: string) => ReactNode;
  onReset: () => void;
  showReset: boolean;
}) {
  const leftCol = placements.filter((placement) => placement.column === 'left');
  const rightCol = placements.filter((placement) => placement.column === 'right');

  return (
    <section className="h-full min-h-0 overflow-hidden rounded-2xl border border-borderSoft/60 bg-panel/45 p-3" aria-label="Focus lane">
      <div className="mb-2 flex h-6 items-center justify-between">
        <p className="text-xs uppercase tracking-[0.15em] text-slate-500">Focus</p>
        {showReset ? (
          <button className="rounded border border-borderSoft/70 px-2 py-0.5 text-[10px] text-slate-400" onClick={onReset}>Reset layout</button>
        ) : null}
      </div>
      <div data-testid="focus-lane-grid" className="thin-scroll h-full min-h-0 overflow-y-auto pb-36">
        <div className="mx-auto grid w-full max-w-[1100px] min-h-full grid-cols-2 gap-3">
          <div className="space-y-3">
            {leftCol.map((placement) => (
              <div key={placement.id} data-testid={`focus-placement-${placement.id}`} className="transition-all duration-300 ease-out">
                {renderWidget(placement.id)}
              </div>
            ))}
          </div>
          <div className="space-y-3">
            {rightCol.map((placement) => (
              <div key={placement.id} data-testid={`focus-placement-${placement.id}`} className="transition-all duration-300 ease-out">
                {renderWidget(placement.id)}
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
