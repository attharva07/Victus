export type TimelineEvent = {
  id: string;
  label: string;
  detail: string;
  createdAt: number;
  tick: number;
  source: 'approvals' | 'command' | 'system';
};

export const timelineSeed: TimelineEvent[] = [
  {
    id: 'ev-1',
    label: 'Executor heartbeat stable',
    detail: 'Automation channels nominal.',
    createdAt: 0,
    tick: -1,
    source: 'system'
  }
];

export function appendTimelineEvent(events: TimelineEvent[], event: Omit<TimelineEvent, 'id'>): TimelineEvent[] {
  const id = `ev-${event.createdAt}-${event.source}`;
  return [{ ...event, id }, ...events];
}
