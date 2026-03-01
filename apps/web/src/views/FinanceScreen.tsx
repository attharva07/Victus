export default function FinanceScreen({ data, authenticated, error }: { data: unknown | null; authenticated: boolean; error?: string }) {
  if (error) {
    return <section className="h-full rounded-xl border border-borderSoft/80 bg-panel/60 p-4 text-sm text-slate-400">{error}</section>;
  }

  if (!authenticated) {
    return <section className="h-full rounded-xl border border-borderSoft/80 bg-panel/60 p-4 text-sm text-slate-400">Login required to load finance summary.</section>;
  }

  if (!data) {
    return <section className="h-full rounded-xl border border-borderSoft/80 bg-panel/60 p-4 text-sm text-slate-400">Loading finance summary from /finance/summary…</section>;
  }

  return (
    <section className="h-full rounded-xl border border-borderSoft/80 bg-panel/60 p-4">
      <h2 className="text-sm uppercase tracking-[0.14em] text-slate-300">Finance summary</h2>
      <pre className="mt-3 max-h-[80vh] overflow-auto text-xs text-slate-300">{JSON.stringify(data, null, 2)}</pre>
    </section>
  );
}
