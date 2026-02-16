import type { TimelineEvent } from '../../data/timelineStore';
import type { DialogueMessage } from '../../data/dialogueStore';
import type { VictusItem } from '../../data/victusStore';
import WidgetCard from './WidgetCard';

export function DialogueWidget({ messages, pinned, onTogglePin }: { messages: DialogueMessage[]; pinned?: boolean; onTogglePin: () => void }) {
  return (
    <WidgetCard title="Dialogue" canExpand={messages.length > 3} pinned={pinned} onTogglePin={onTogglePin} testId="widget-dialogue" defaultExpanded>
      <ul className="space-y-2 text-xs">
        {messages.slice(-10).map((message) => (
          <li key={message.id} className="rounded-md border border-borderSoft/70 bg-panelSoft/40 px-2 py-1.5">
            <p className="text-[10px] uppercase tracking-wide text-slate-500">{message.role}</p>
            <p className="text-slate-200">{message.text}</p>
          </li>
        ))}
      </ul>
    </WidgetCard>
  );
}

export function SystemOverviewWidget({ reminders, approvals, failures, workflows, pinned, onTogglePin }: { reminders: number; approvals: number; failures: number; workflows: number; pinned?: boolean; onTogglePin: () => void }) {
  return (
    <WidgetCard title="System Overview" canExpand={false} pinned={pinned} onTogglePin={onTogglePin} testId="widget-system-overview">
      <ul className="space-y-1 text-xs text-slate-300">
        <li>Reminders active: {reminders}</li>
        <li>Approvals pending: {approvals}</li>
        <li>Open failures: {failures}</li>
        <li>Workflows active: {workflows}</li>
      </ul>
    </WidgetCard>
  );
}

export function TimelineWidget({ events, pinned, onTogglePin }: { events: TimelineEvent[]; pinned?: boolean; onTogglePin: () => void }) {
  return (
    <WidgetCard title="Timeline" canExpand={events.length > 0} pinned={pinned} onTogglePin={onTogglePin} testId="widget-timeline" defaultExpanded>
      <div className="space-y-2 text-xs text-slate-300">
        {events.slice(0, 12).map((event) => (
          <div key={event.id} className="rounded border border-borderSoft/60 bg-panelSoft/35 px-2 py-1.5">
            <p>{event.label}</p>
            <p className="text-[10px] text-slate-500">{event.detail}</p>
          </div>
        ))}
      </div>
    </WidgetCard>
  );
}

export function HealthPulseWidget({ failures, pinned, onTogglePin }: { failures: VictusItem[]; pinned?: boolean; onTogglePin: () => void }) {
  return (
    <WidgetCard title="Health Pulse" canExpand={failures.length > 2} pinned={pinned} onTogglePin={onTogglePin} testId="widget-health-pulse">
      <ul className="space-y-2 text-xs text-rose-100">
        {failures.length === 0 ? <li className="text-slate-300">No unresolved failures.</li> : failures.map((item) => <li key={item.id} className="rounded border border-rose-800/40 px-2 py-1">{item.title}</li>)}
      </ul>
    </WidgetCard>
  );
}
