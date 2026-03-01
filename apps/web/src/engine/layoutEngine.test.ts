import { computeAdaptiveLayout } from './layoutEngine';
import type { AdaptiveItem } from './adaptiveScore';

const now = Date.now();

const mockItems: AdaptiveItem[] = [
  { id: 'f1', kind: 'failure', title: 'Failure', detail: 'x', status: 'open', urgency: 95, confidenceImpact: -40, severity: 'critical', updatedAt: now, actions: ['open'] },
  { id: 'a1', kind: 'approval', title: 'Approval', detail: 'x', status: 'pending', urgency: 70, confidenceImpact: -10, updatedAt: now, actions: ['approve', 'deny'] },
  { id: 'r1', kind: 'reminder', title: 'Reminder', detail: 'x', status: 'pending', urgency: 85, confidenceImpact: -5, updatedAt: now, actions: ['done'] },
  { id: 't1', kind: 'timeline', title: 'Timeline', detail: 'x', status: 'active', urgency: 40, confidenceImpact: 10, updatedAt: now, actions: ['open'] }
];

describe('layout engine', () => {
  it('forces failures into focus and keeps timeline stream always present', () => {
    const plan = computeAdaptiveLayout(mockItems, {});
    expect(plan.focus.map((card) => card.item.id)).toContain('f1');
    expect(plan.timeline.map((card) => card.item.id)).toContain('t1');
  });

  it('keeps approvals in context unless urgency crosses threshold', () => {
    const normal = computeAdaptiveLayout(mockItems, {});
    expect(normal.context.map((card) => card.item.id)).toContain('a1');

    const escalated = computeAdaptiveLayout([{ ...mockItems[1], urgency: 90 }, mockItems[0], mockItems[2], mockItems[3]], {});
    expect(escalated.focus.map((card) => card.item.id)).toContain('a1');
  });
});
