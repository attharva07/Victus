import type { LayoutPlan } from './types';

export const defaultLayoutPlan: LayoutPlan = {
  preset: 'P2',
  generatedAt: Date.now(),
  ttlSeconds: 120,
  placements: [
    { id: 'system_overview', zone: 'center', size: 'L', colSpan: 1, priority: 1 },
    { id: 'timeline', zone: 'center', size: 'M', colSpan: 1, priority: 2 },
    { id: 'world_tldr', zone: 'center', size: 'S', colSpan: 1, priority: 3 },
    { id: 'reminders', zone: 'right', size: 'S', colSpan: 1, priority: 10 },
    { id: 'alerts', zone: 'right', size: 'S', colSpan: 1, priority: 11 },
    { id: 'approvals', zone: 'right', size: 'S', colSpan: 1, priority: 12 },
    { id: 'workflows', zone: 'right', size: 'S', colSpan: 1, priority: 13 },
    { id: 'failures', zone: 'right', size: 'S', colSpan: 1, priority: 14 }
  ]
};

export default defaultLayoutPlan;
