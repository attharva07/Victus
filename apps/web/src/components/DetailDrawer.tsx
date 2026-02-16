import type { VictusItem } from '../data/victusStore';

type DrawerAction = { label: string; onClick: () => void };

const typeLabel: Record<VictusItem['kind'], string> = {
  reminder: 'REMINDER',
  alert: 'ALERT',
  event: 'EVENT',
  approval: 'APPROVAL',
  workflow: 'WORKFLOW',
  failure: 'FAILURE'
};

export default function DetailDrawer({ item, onClose, actions }: { item: VictusItem; onClose: () => void; actions: DrawerAction[] }) {
  return (
    <aside className="flex h-full flex-col rounded-xl border border-borderSoft/80 bg-panel px-4 py-3">
      <div className="flex items-start justify-between">
        <h3 className="text-sm font-medium text-slate-100">Item Details</h3>
        <button
          onClick={onClose}
          className="rounded-md border border-borderSoft/70 px-2 py-0.5 text-xs text-slate-400 hover:bg-panelSoft focus-visible:outline focus-visible:outline-2 focus-visible:outline-cyan-500"
          aria-label="Close details"
        >
          X
        </button>
      </div>

      <div className="subtle-scrollbar mt-4 flex-1 space-y-3 overflow-y-auto pb-20">
        <span className="inline-flex rounded-full border border-borderSoft bg-panelSoft/60 px-2 py-0.5 text-[10px] tracking-[0.15em] text-slate-300">
          {typeLabel[item.kind]}
        </span>

        <div>
          <h4 className="text-base font-medium text-slate-100">{item.title}</h4>
          <p className="mt-2 text-sm text-slate-400">{item.detail}</p>
        </div>

        <div className="rounded-lg border border-borderSoft/50 bg-panelSoft/40 p-3 text-xs text-slate-400">
          <p>Assigned by: {item.source}</p>
          <p className="mt-1">Domain: {item.domain}</p>
          <p className="mt-1">Created: {item.createdAt}</p>
          <p className="mt-1">Updated: {item.updatedAt}</p>
          <p className="mt-1">Time: {item.timeLabel}</p>
        </div>
      </div>

      <div className="sticky bottom-0 mt-3 flex flex-wrap gap-2 border-t border-borderSoft/60 bg-panel pt-3">
        {actions.map((action) => (
          <button
            key={action.label}
            onClick={action.onClick}
            className="rounded-md border border-borderSoft/70 bg-panelSoft/70 px-3 py-1.5 text-xs text-slate-200 hover:bg-slate-700/40 focus-visible:outline focus-visible:outline-2 focus-visible:outline-cyan-500"
          >
            {action.label}
          </button>
        ))}
      </div>
    </aside>
  );
}
