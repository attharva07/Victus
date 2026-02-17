import { useMemo, useState } from 'react';
import type { AdaptiveItem } from '../engine/adaptiveScore';
import { computeAdaptiveLayout, type PinState } from '../engine/layoutEngine';

export type TimelineEvent = { id: string; label: string; detail: string; createdAt: number };

const now = Date.now();

const seedItems: AdaptiveItem[] = [
  { id: 'failure-1', kind: 'failure', title: 'Orchestrator retry exhausted', detail: 'Last retry exceeded policy backoff window.', status: 'open', urgency: 90, confidenceImpact: -40, severity: 'critical', updatedAt: now - 2 * 60_000, actions: ['open'] },
  { id: 'approval-1', kind: 'approval', title: 'Filesystem tool scope adjustment', detail: 'Grant wider read/write scope for migration script.', status: 'pending', urgency: 74, confidenceImpact: -10, updatedAt: now - 5 * 60_000, actions: ['approve', 'deny'] },
  { id: 'alert-1', kind: 'alert', title: 'Memory latency drift', detail: '95th percentile latency is up 12%.', status: 'open', urgency: 67, confidenceImpact: -18, severity: 'warning', updatedAt: now - 15 * 60_000, actions: ['open'] },
  { id: 'reminder-1', kind: 'reminder', title: 'Approve onboarding policy edits', detail: 'Due today 2:00 PM', status: 'pending', urgency: 82, confidenceImpact: -8, updatedAt: now - 12 * 60_000, actions: ['done'] },
  { id: 'workflow-1', kind: 'workflow', title: 'Weekly planning synthesis', detail: 'Step 3/5 · 60%', status: 'paused', urgency: 63, confidenceImpact: 20, updatedAt: now - 40 * 60_000, actions: ['resume'] },
  { id: 'dialogue-1', kind: 'dialogue', title: 'Dialogue', detail: 'Victus is active. Issue a command when ready.', status: 'active', urgency: 45, confidenceImpact: 18, updatedAt: now - 1 * 60_000, actions: ['open'] },
  { id: 'timeline-stream', kind: 'timeline', title: 'Timeline', detail: 'Truth stream of system + operator actions.', status: 'active', urgency: 50, confidenceImpact: 12, updatedAt: now - 1 * 60_000, actions: ['open'] }
];

const seedTimeline: TimelineEvent[] = [
  { id: 't1', label: 'Executor heartbeat stable', detail: 'Automation channels nominal.', createdAt: now - 30 * 60_000 },
  { id: 't2', label: 'Team planning sync', detail: 'Agenda locked for tomorrow.', createdAt: now - 20 * 60_000 },
  { id: 't3', label: 'Inbox triage complete', detail: '12 items processed.', createdAt: now - 45 * 60_000 }
];

function makeEvent(label: string, detail: string): TimelineEvent {
  return { id: `timeline-${Date.now()}-${Math.random().toString(16).slice(2)}`, label, detail, createdAt: Date.now() };
}

export function useUIState() {
  const [items, setItems] = useState<AdaptiveItem[]>(seedItems);
  const [timelineEvents, setTimelineEvents] = useState<TimelineEvent[]>(seedTimeline);
  const [pinState, setPinState] = useState<PinState>({});

  const layout = useMemo(() => computeAdaptiveLayout(items, pinState), [items, pinState]);

  const addTimeline = (label: string, detail: string) => {
    setTimelineEvents((prev) => [makeEvent(label, detail), ...prev]);
    setItems((prev) => prev.map((item) => (item.kind === 'timeline' ? { ...item, updatedAt: Date.now() } : item)));
  };

  const touchItem = (id: string, mutate?: (item: AdaptiveItem) => AdaptiveItem) => {
    setItems((prev) => prev.map((item) => (item.id === id ? mutate?.({ ...item, updatedAt: Date.now() }) ?? { ...item, updatedAt: Date.now() } : item)));
  };

  const actions = {
    approve: (id: string) => {
      const target = items.find((item) => item.id === id);
      setItems((prev) => prev.filter((item) => item.id !== id));
      if (target) addTimeline(`Approval resolved: ${target.title} (approved)`, 'Approval approved by operator.');
    },
    deny: (id: string) => {
      const target = items.find((item) => item.id === id);
      setItems((prev) => prev.filter((item) => item.id !== id));
      if (target) addTimeline(`Approval resolved: ${target.title} (denied)`, 'Approval denied by operator.');
    },
    done: (id: string) => {
      const target = items.find((item) => item.id === id);
      setItems((prev) => prev.filter((item) => item.id !== id));
      if (target) addTimeline(`Done: ${target.title}`, 'Item marked done and removed from adaptive lanes.');
    },
    resume: (id: string) => {
      touchItem(id, (item) => ({ ...item, status: 'active', urgency: Math.min(100, item.urgency + 10), detail: 'Resumed · step advanced' }));
      const target = items.find((item) => item.id === id);
      if (target) addTimeline(`Workflow resumed: ${target.title}`, 'Workflow status changed to active.');
    },
    togglePin: (id: string) => {
      setPinState((prev) => {
        if (prev[id]) {
          const next = { ...prev };
          delete next[id];
          return next;
        }
        const focusIndex = layout.focus.findIndex((card) => card.item.id === id);
        const contextIndex = layout.context.findIndex((card) => card.item.id === id);
        if (focusIndex >= 0) return { ...prev, [id]: { lane: 'focus', order: focusIndex } };
        return { ...prev, [id]: { lane: 'context', order: Math.max(0, contextIndex) } };
      });
    }
  };

  return {
    items,
    timelineEvents,
    layout,
    pinState,
    actions
  };
}
