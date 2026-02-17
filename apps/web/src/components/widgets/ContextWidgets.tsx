import type { AlertItem, ApprovalItem, FailureItem, ReminderItem, WorkflowItem } from '../../types/victus-ui';
import WidgetCard from './WidgetCard';

function emptyState(label: string) {
  return <p className="text-[11px] text-slate-500">No {label.toLowerCase()} right now.</p>;
}

export function RemindersWidget({ items, onDone }: { items: ReminderItem[]; onDone?: (id: string) => void }) {
  return (
    <WidgetCard title={`Reminders (${items.length})`} canExpand={items.length > 2} testId="widget-reminders" scrollBody={false} className={items.length === 0 ? 'bg-panelSoft/50' : undefined}>
      {items.length === 0 ? emptyState('Reminders') : <ul className="space-y-2 text-xs">{items.map((item) => <li key={item.id}><span>{item.title}</span>{onDone ? <button className="ml-2 text-[10px] text-emerald-300" onClick={() => onDone(item.id)}>done</button> : null}</li>)}</ul>}
    </WidgetCard>
  );
}

export function AlertsWidget({ items, onAck }: { items: AlertItem[]; onAck?: (id: string) => void }) {
  return (
    <WidgetCard title={`Alerts (${items.length})`} canExpand={items.length > 2} testId="widget-alerts" scrollBody={false} className={items.length === 0 ? 'bg-panelSoft/50' : undefined}>
      {items.length === 0 ? emptyState('Alerts') : <ul className="space-y-2 text-xs">{items.map((item) => <li key={item.id}><span>{item.title}</span>{onAck ? <button className="ml-2 text-[10px] text-cyan-300" onClick={() => onAck(item.id)}>ack</button> : null}</li>)}</ul>}
    </WidgetCard>
  );
}

export function ApprovalsWidget({ items, onApprove, onDeny }: { items: ApprovalItem[]; onApprove: (id: string) => void; onDeny: (id: string) => void }) {
  return (
    <WidgetCard title={`Approvals (${items.length})`} canExpand={items.length > 1} testId="widget-approvals" defaultExpanded scrollBody={false} className={items.length === 0 ? 'bg-panelSoft/50' : undefined}>
      {items.length === 0 ? (
        emptyState('Approvals')
      ) : (
        <div className="space-y-2 text-xs">
          {items.map((item) => (
            <div key={item.id} className="rounded border border-borderSoft/60 px-2 py-1.5">
              <p>{item.title}</p>
              <div className="mt-1 flex gap-1">
                <button type="button" className="rounded border border-emerald-700/40 px-2 py-0.5 text-[10px] text-emerald-200" onClick={() => onApprove(item.id)}>Approve</button>
                <button type="button" className="rounded border border-rose-700/40 px-2 py-0.5 text-[10px] text-rose-200" onClick={() => onDeny(item.id)}>Deny</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </WidgetCard>
  );
}

export function FailuresWidget({ items }: { items: FailureItem[] }) {
  return (
    <WidgetCard title={`Failures (${items.length})`} canExpand={items.length > 2} testId="widget-failures" scrollBody={false} className={items.length === 0 ? 'bg-panelSoft/50' : undefined}>
      {items.length === 0 ? emptyState('Failures') : <ul className="space-y-2 text-xs">{items.map((item) => <li key={item.id}>{item.title}</li>)}</ul>}
    </WidgetCard>
  );
}

export function WorkflowsWidget({ items, onResume, onPause, onAdvanceStep }: { items: WorkflowItem[]; onResume?: (id: string) => void; onPause?: (id: string) => void; onAdvanceStep?: (id: string) => void }) {
  return (
    <WidgetCard title={`Workflows (${items.length})`} canExpand={items.length > 2} testId="widget-workflows" scrollBody={false} className={items.length === 0 ? 'bg-panelSoft/50' : undefined}>
      {items.length === 0 ? emptyState('Workflows') : <ul className="space-y-2 text-xs">{items.map((item) => <li key={item.id}><span>{item.title}</span>{onResume ? <button className="ml-2 text-[10px] text-cyan-300" onClick={() => onResume(item.id)}>resume</button> : null}{onPause ? <button className="ml-2 text-[10px] text-amber-300" onClick={() => onPause(item.id)}>pause</button> : null}{onAdvanceStep ? <button className="ml-2 text-[10px] text-violet-300" onClick={() => onAdvanceStep(item.id)}>advance</button> : null}</li>)}</ul>}
    </WidgetCard>
  );
}
