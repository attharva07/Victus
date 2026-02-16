import { useState } from 'react';

const nodes = ['vault/', 'vault/notes/', 'vault/notes/weekly.md', 'vault/finance/', 'vault/finance/ledger.csv'];

export default function FilesScreen() {
  const [opened, setOpened] = useState<string | null>(null);

  return (
    <section className="h-full rounded-xl border border-borderSoft/80 bg-panel/60 p-3">
      <div className="h-full rounded-lg border border-borderSoft/70 bg-panel p-4">
        <h2 className="text-sm uppercase tracking-[0.14em] text-slate-300">Files</h2>
        <ul className="mt-3 space-y-2 text-sm text-slate-300">
          {nodes.map((node) => (
            <li key={node} className="flex items-center justify-between rounded-md border border-borderSoft/70 bg-panelSoft/40 px-3 py-2">
              <span>{node}</span>
              <button className="text-xs text-cyan-200 hover:text-cyan-100" onClick={() => setOpened(node)}>
                Open
              </button>
            </li>
          ))}
        </ul>
        <p className="mt-4 text-xs text-slate-500">{opened ? `Opened ${opened}` : 'Select a file node to open.'}</p>
      </div>
    </section>
  );
}
