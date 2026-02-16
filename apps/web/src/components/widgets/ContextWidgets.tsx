import type { AlertItem, ApprovalItem, FailureItem, ReminderItem, WorkflowItem } from '../../state/mockState';
import WidgetCard from './WidgetCard';

export function RemindersWidget({ items }: { items: ReminderItem[] }) {
  return <WidgetCard title={`Reminders (${items.length})`} canExpand={items.length > 2} testId="widget-reminders"><ul className="space-y-2 text-xs">{items.map((item) => <li key={item.id}>{item.title}</li>)}</ul></WidgetCard>;
}

export function AlertsWidget({ items }: { items: AlertItem[] }) {
  return <WidgetCard title={`Alerts (${items.length})`} canExpand={items.length > 2} testId="widget-alerts"><ul className="space-y-2 text-xs">{items.map((item) => <li key={item.id}>{item.title}</li>)}</ul></WidgetCard>;
}

export function ApprovalsWidget({ items, onApprove, onDeny }: { items: ApprovalItem[]; onApprove: (id: string) => void; onDeny: (id: string) => void }) {
  return (
    <WidgetCard title={`Approvals (${items.length})`} canExpand={items.length > 1} testId="widget-approvals" defaultExpanded>
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
    </WidgetCard>
  );
}

export function WorkflowsWidget({ items }: { items: WorkflowItem[] }) {
  return <WidgetCard title={`Workflows (${items.length})`} canExpand={items.length > 2} testId="widget-workflows"><ul className="space-y-2 text-xs">{items.map((item) => <li key={item.id}>{item.title}</li>)}</ul></WidgetCard>;
}

export function FailuresWidget({ items }: { items: FailureItem[] }) {
  return <WidgetCard title={`Failures (${items.length})`} canExpand={items.length > 2} testId="widget-failures"><ul className="space-y-2 text-xs">{items.map((item) => <li key={item.id}>{item.title}</li>)}</ul></WidgetCard>;
}
