export type VictusView = 'overview' | 'memories' | 'finance' | 'files' | 'camera';

const railItems: { icon: string; label: string; view: VictusView }[] = [
  { icon: '◉', label: 'Overview', view: 'overview' },
  { icon: '⌘', label: 'Memories', view: 'memories' },
  { icon: '◌', label: 'Finance', view: 'finance' },
  { icon: '⟡', label: 'Files', view: 'files' },
  { icon: '⋯', label: 'Camera', view: 'camera' }
];

export default function LeftRail({ activeView, onChangeView }: { activeView: VictusView; onChangeView: (view: VictusView) => void }) {
  return (
    <aside className="h-full w-16 border-r border-borderSoft/70 bg-panel/70 px-3 py-4">
      <div className="flex h-full flex-col items-center gap-4">
        {railItems.map((item) => (
          <button
            key={item.view}
            className={`h-9 w-9 rounded-lg border text-sm text-slate-300 transition hover:bg-slate-800/70 focus-visible:outline focus-visible:outline-2 focus-visible:outline-cyan-500 ${
              activeView === item.view ? 'border-cyan-500/70 bg-slate-800/80' : 'border-borderSoft/80'
            }`}
            aria-label={item.label}
            onClick={() => onChangeView(item.view)}
          >
            {item.icon}
          </button>
        ))}
      </div>
    </aside>
  );
}
