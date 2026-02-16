import type { ReactNode } from 'react';
import type { WidgetId } from '../../layout/types';

export default function ContextLane({ orderedIds, renderWidget }: { orderedIds: WidgetId[]; renderWidget: (id: WidgetId) => ReactNode }) {
  return (
    <aside className="h-full min-h-0 overflow-hidden rounded-2xl border border-borderSoft/60 bg-panel/30 p-3">
      <section data-testid="context-stack-container" className="flex h-full min-h-0 flex-col overflow-hidden rounded-xl border border-borderSoft/70 bg-panel/80 px-3 py-2">
        <header className="mb-2">
          <h2 className="text-xs uppercase tracking-[0.15em] text-slate-300">Context Stack</h2>
        </header>

        <div data-testid="right-context-scroll" className="thin-scroll h-full min-h-0 overflow-y-auto">
          <div className="space-y-2 pb-24">
            {orderedIds.map((id) => (
              <div key={id}>{renderWidget(id)}</div>
            ))}
          </div>
        </div>
      </section>
    </aside>
  );
}
