import type { ApprovalItem, DialogueMessage, FailureItem, ReminderItem, TimelineEvent, WorkflowItem } from '../../state/mockState';
import WidgetCard from './WidgetCard';

export function DialogueWidget({ messages, pinned, onTogglePin }: { messages: DialogueMessage[]; pinned?: boolean; onTogglePin: () => void }) {
  return (
    <WidgetCard title="Dialogue" canExpand={messages.length > 3} pinned={pinned} onTogglePin={onTogglePin} testId="widget-dialogue" defaultExpanded>
      <ul className="space-y-2 text-xs">
        {messages.slice(-8).map((message) => (
          <li key={message.id} className="rounded-md border border-borderSoft/70 bg-panelSoft/40 px-2 py-1.5">
            <p className="text-[10px] uppercase tracking-wide text-slate-500">{message.role}</p>
            <p className="text-slate-200">{message.text}</p>
          </li>
        ))}
      </ul>
    </WidgetCard>
  );
}

export function TimelineWidget({ events, pinned, onTogglePin }: { events: TimelineEvent[]; pinned?: boolean; onTogglePin: () => void }) {
  const grouped = {
    Today: events.filter((item) => item.bucket === 'Today'),
    Upcoming: events.filter((item) => item.bucket === 'Upcoming'),
    Completed: events.filter((item) => item.bucket === 'Completed')
  };

  return (
    <WidgetCard title="Timeline" canExpand={events.length > 2} pinned={pinned} onTogglePin={onTogglePin} testId="widget-timeline" defaultExpanded>
      <div className="space-y-2 text-xs text-slate-300">
        {(Object.keys(grouped) as Array<keyof typeof grouped>).map((bucket) => (
          <div key={bucket}>
            <p className="mb-1 text-[10px] uppercase tracking-wide text-slate-500">{bucket}</p>
            <div className="space-y-1">
              {grouped[bucket].slice(0, 4).map((event) => (
                <div key={event.id} className="rounded border border-borderSoft/60 bg-panelSoft/35 px-2 py-1.5">
                  <p>{event.label}</p>
                  <p className="text-[10px] text-slate-500">{event.detail}</p>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </WidgetCard>
  );
}

export function HealthPulseWidget({ failures, pinned, onTogglePin }: { failures: FailureItem[]; pinned?: boolean; onTogglePin: () => void }) {
  return (
    <WidgetCard title="Health Pulse" canExpand={failures.length > 1} pinned={pinned} onTogglePin={onTogglePin} testId="widget-health-pulse">
      <ul className="space-y-2 text-xs text-rose-100">
        {failures.length === 0 ? <li className="text-slate-300">No unresolved failures.</li> : failures.map((item) => <li key={item.id}>{item.title} · {item.severity}</li>)}
      </ul>
    </WidgetCard>
  );
}

export function SystemOverviewWidget({ reminders, approvals, failures, workflows, pinned, onTogglePin }: { reminders: number; approvals: number; failures: number; workflows: number; pinned?: boolean; onTogglePin: () => void }) {
  return (
    <WidgetCard title="System Overview" canExpand={false} pinned={pinned} onTogglePin={onTogglePin} testId="widget-system-overview">
      <ul className="space-y-1 text-xs text-slate-300">
        <li>Reminders: {reminders}</li><li>Approvals: {approvals}</li><li>Failures: {failures}</li><li>Workflows: {workflows}</li>
      </ul>
    </WidgetCard>
  );
}

export function WorldTldrWidget({ items, pinned, onTogglePin }: { items: string[]; pinned?: boolean; onTogglePin: () => void }) {
  return (
    <WidgetCard title="World TLDR" canExpand={items.length > 2} pinned={pinned} onTogglePin={onTogglePin} testId="widget-world-tldr">
      <ul className="space-y-1 text-xs text-slate-300">{items.slice(0, 3).map((item, index) => <li key={`${item}-${index}`}>• {item}</li>)}</ul>
    </WidgetCard>
  );
}

export function WorkflowsBoardWidget({ items, pinned, onTogglePin }: { items: WorkflowItem[]; pinned?: boolean; onTogglePin: () => void }) {
  return (
    <WidgetCard title="Workflows Board" canExpand={items.length > 1} pinned={pinned} onTogglePin={onTogglePin} testId="widget-workflows-board">
      <div className="space-y-2 text-xs">
        {items.map((item) => (
          <div key={item.id} className="rounded border border-borderSoft/60 px-2 py-1.5">
            <p>{item.title}</p><p className="text-[10px] text-slate-500">{item.stepLabel} · {item.progress}%</p>
            <button type="button" className="mt-1 rounded border border-cyan-700/40 px-2 py-0.5 text-[10px] text-cyan-200">Resume</button>
          </div>
        ))}
      </div>
    </WidgetCard>
  );
}

export function RemindersPanelWidget({ items, onDone, pinned, onTogglePin }: { items: ReminderItem[]; onDone: (id: string) => void; pinned?: boolean; onTogglePin: () => void }) {
  return (
    <WidgetCard title="Reminders Panel" canExpand={items.length > 1} pinned={pinned} onTogglePin={onTogglePin} testId="widget-reminders-panel">
      <ul className="space-y-2 text-xs">
        {items.map((item) => (
          <li key={item.id} className="rounded border border-borderSoft/60 px-2 py-1.5">
            <p>{item.title}</p><p className="text-[10px] text-slate-500">{item.due} · {item.urgency}</p>
            <button type="button" className="mt-1 rounded border border-emerald-700/40 px-2 py-0.5 text-[10px] text-emerald-200" onClick={() => onDone(item.id)}>Mark done</button>
          </li>
        ))}
      </ul>
    </WidgetCard>
  );
}

export function ApprovalsPanelWidget({ items, onApprove, onDeny, pinned, onTogglePin }: { items: ApprovalItem[]; onApprove: (id: string) => void; onDeny: (id: string) => void; pinned?: boolean; onTogglePin: () => void }) {
  return (
    <WidgetCard title="Approvals Panel" canExpand={items.length > 1} pinned={pinned} onTogglePin={onTogglePin} testId="widget-approvals-panel">
      <div className="space-y-2 text-xs">
        {items.map((item) => (
          <div key={item.id} className="rounded border border-borderSoft/60 px-2 py-1.5">
            <p>{item.title}</p><p className="text-[10px] text-slate-500">{item.detail}</p>
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
