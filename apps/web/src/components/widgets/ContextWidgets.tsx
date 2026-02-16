import { useState } from 'react';
import type { VictusItem } from '../../data/victusStore';
import WidgetCard from './WidgetCard';

function ItemButton({ item, onClick }: { item: VictusItem; onClick: () => void }) {
  return (
    <button className="w-full rounded border border-borderSoft/60 bg-panelSoft/50 px-2 py-1 text-left text-xs text-slate-300" onClick={onClick}>
      <p>{item.title}</p>
      <p className="text-[10px] text-slate-500">{item.timeLabel}</p>
    </button>
  );
}

export function RemindersWidget({ items }: { items: VictusItem[] }) {
  const [openId, setOpenId] = useState<string>();
  return (
    <WidgetCard title={`Reminders (${items.length})`} canExpand={items.length > 2} testId="widget-reminders">
      <ul className="space-y-2">
        {items.map((item) => (
          <li key={item.id}>
            <ItemButton item={item} onClick={() => setOpenId(openId === item.id ? undefined : item.id)} />
            {openId === item.id ? <p className="mt-1 text-xs text-slate-400">{item.detail}</p> : null}
          </li>
        ))}
      </ul>
    </WidgetCard>
  );
}

export function AlertsWidget({ items }: { items: VictusItem[] }) {
  const [openId, setOpenId] = useState<string>();
  return (
    <WidgetCard title={`Alerts (${items.length})`} canExpand={items.length > 2} testId="widget-alerts">
      <ul className="space-y-2">
        {items.map((item) => (
          <li key={item.id}>
            <ItemButton item={item} onClick={() => setOpenId(openId === item.id ? undefined : item.id)} />
            {openId === item.id ? <p className="mt-1 text-xs text-slate-400">{item.detail}</p> : null}
          </li>
        ))}
      </ul>
    </WidgetCard>
  );
}

export function ApprovalsWidget({ items, onApprove, onDeny }: { items: VictusItem[]; onApprove: (id: string) => void; onDeny: (id: string) => void }) {
  const [resolving, setResolving] = useState<Record<string, boolean>>({});
  const pending = items.filter((item) => item.approvalState === 'pending');
  const resolved = items.filter((item) => item.approvalState && item.approvalState !== 'pending');

  const resolve = (id: string, action: 'approve' | 'deny') => {
    setResolving((previous) => ({ ...previous, [id]: true }));
    window.setTimeout(() => {
      if (action === 'approve') onApprove(id);
      else onDeny(id);
    }, 220);
  };

  return (
    <WidgetCard title={`Approvals (${pending.length})`} canExpand={pending.length + resolved.length > 2} testId="widget-approvals" defaultExpanded>
      <div className="space-y-2 text-xs">
        {pending.map((item) => (
          <div key={item.id} className={`rounded border border-borderSoft/60 px-2 py-1.5 transition-all duration-200 ${resolving[item.id] ? 'translate-x-1 opacity-0' : 'opacity-100'}`}>
            <p className="text-slate-200">{item.title}</p>
            <div className="mt-1 flex gap-1">
              <button className="rounded border border-emerald-700/40 px-2 py-0.5 text-[10px] text-emerald-200" onClick={() => resolve(item.id, 'approve')}>Approve</button>
              <button className="rounded border border-rose-700/40 px-2 py-0.5 text-[10px] text-rose-200" onClick={() => resolve(item.id, 'deny')}>Deny</button>
            </div>
          </div>
        ))}
        {resolved.length > 0 ? <p className="text-[10px] uppercase tracking-wide text-slate-500">Resolved: {resolved.length}</p> : null}
      </div>
    </WidgetCard>
  );
}

export function WorkflowsWidget({ items }: { items: VictusItem[] }) {
  return (
    <WidgetCard title={`Workflows (${items.length})`} canExpand={items.length > 2} testId="widget-workflows">
      <ul className="space-y-2 text-xs text-slate-300">{items.map((item) => <li key={item.id}>{item.title} · {item.timeLabel}</li>)}</ul>
    </WidgetCard>
  );
}

export function FailuresWidget({ items }: { items: VictusItem[] }) {
  return (
    <WidgetCard title={`Failures (${items.length})`} canExpand={items.length > 2} testId="widget-failures">
      <ul className="space-y-2 text-xs text-rose-100">{items.map((item) => <li key={item.id}>{item.title}</li>)}</ul>
    </WidgetCard>
  );
}
