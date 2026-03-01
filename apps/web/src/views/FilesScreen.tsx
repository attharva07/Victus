export default function FilesScreen({ data, authenticated, error }: { data: string[] | null; authenticated: boolean; error?: string }) {
  if (error) {
    return <section className="h-full rounded-xl border border-borderSoft/80 bg-panel/60 p-4 text-sm text-slate-400">{error}</section>;
  }

  if (!authenticated) {
    return <section className="h-full rounded-xl border border-borderSoft/80 bg-panel/60 p-4 text-sm text-slate-400">Login required to list files.</section>;
  }

  if (!data) {
    return <section className="h-full rounded-xl border border-borderSoft/80 bg-panel/60 p-4 text-sm text-slate-400">Loading files from /files/list…</section>;
  }

  return (
    <section className="h-full rounded-xl border border-borderSoft/80 bg-panel/60 p-4">
      <h2 className="text-sm uppercase tracking-[0.14em] text-slate-300">Files</h2>
      <ul className="mt-3 space-y-2 text-sm text-slate-300">
        {data.map((filePath) => (
          <li key={filePath} className="rounded-md border border-borderSoft/70 bg-panelSoft/40 px-3 py-2">{filePath}</li>
        ))}
      </ul>
    </section>
  );
}
