const icons = ['◉', '⌘', '◌', '⟡', '⋯'];

export default function LeftRail() {
  return (
    <aside className="h-full w-16 border-r border-borderSoft/70 bg-panel/70 px-3 py-4">
      <div className="flex h-full flex-col items-center gap-4">
        {icons.map((icon, index) => (
          <button
            key={icon + index}
            className="h-9 w-9 rounded-lg border border-borderSoft/80 text-sm text-slate-300 transition hover:bg-slate-800/70"
            aria-label={`rail-icon-${index}`}
          >
            {icon}
          </button>
        ))}
      </div>
    </aside>
  );
}
