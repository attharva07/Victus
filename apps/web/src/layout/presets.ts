import type { LayoutPlan } from './types';

export const defaultLayoutPlan: LayoutPlan = {
  preset: 'P2',
  generatedAt: Date.now(),
  ttlSeconds: 300,
  placements: [
    { id: 'systemOverview', zone: 'center', size: 'L', priority: 0 },
    { id: 'timeline', zone: 'center', size: 'M', priority: 1 },
    { id: 'worldTldr', zone: 'center', size: 'S', priority: 2 },
    { id: 'reminders', zone: 'right', size: 'S', priority: 0 },
    { id: 'alerts', zone: 'right', size: 'S', priority: 1 },
    { id: 'approvals', zone: 'right', size: 'S', priority: 2 },
    { id: 'workflows', zone: 'right', size: 'S', priority: 3 },
    { id: 'failures', zone: 'right', size: 'S', priority: 4 }
  ]
};

export default defaultLayoutPlan;
