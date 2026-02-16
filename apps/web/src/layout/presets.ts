import type { LayoutPlan } from './types';

// P1: LeftRail | CenterStack | RightStack | BottomStrip + fixed CommandDock
export const defaultLayoutPlan: LayoutPlan = {
  preset: 'P1',
  generatedAt: Date.now(),
  ttlSeconds: 300,
  splitColumns: 'balanced',
  placements: [
    { id: 'system_overview', zone: 'center', size: 'L', priority: 1 },
    { id: 'dialogue', zone: 'center', size: 'S', priority: 2 },
    { id: 'timeline', zone: 'center', size: 'M', priority: 3 },
    { id: 'world_tldr', zone: 'center', size: 'S', priority: 4 },
    { id: 'reminders', zone: 'right', size: 'S', priority: 1 },
    { id: 'alerts', zone: 'right', size: 'S', priority: 2 },
    { id: 'approvals', zone: 'right', size: 'XS', priority: 3 },
    { id: 'workflows', zone: 'right', size: 'S', priority: 4 },
    { id: 'failures', zone: 'right', size: 'S', priority: 5 }
  ]
};

export default defaultLayoutPlan;
