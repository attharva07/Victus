import { describe, expect, it } from 'vitest';
import { generateLayoutPlan } from './engine';
import type { LayoutSignals } from './signals';

const baseSignals: LayoutSignals = {
  remindersCount: 2,
  remindersDueToday: 1,
  alertsCount: 1,
  alertsSeverity: 'low',
  failuresCount: 0,
  failuresSeverity: 'none',
  approvalsPending: 1,
  workflowsActive: 1,
  confidence: 'stable',
  confidenceScore: 82,
  dialogueOpen: false,
  focusMode: 'default',
  updatedAt: 1000
};

describe('layout engine phase 4B hybrid policy + scoring', () => {
  it('unstable confidence selects preset P2', () => {
    const plan = generateLayoutPlan({ ...baseSignals, confidence: 'unstable', confidenceScore: 35 });
    expect(plan.preset).toBe('P2');
  });

  it('dialogue open with high confidence selects P3 and dialogue XL active', () => {
    const plan = generateLayoutPlan({ ...baseSignals, dialogueOpen: true, confidenceScore: 88, updatedAt: 2000 });
    const dialogue = plan.placements.find((placement) => placement.id === 'dialogue');

    expect(plan.preset).toBe('P3');
    expect(plan.activeCardId).toBe('dialogue');
    expect(dialogue?.size).toBe('XL');
  });

  it('high failure severity makes failures largest right-side card', () => {
    const plan = generateLayoutPlan({
      ...baseSignals,
      failuresCount: 3,
      failuresSeverity: 'high',
      alertsCount: 1,
      approvalsPending: 1,
      updatedAt: 3000
    });

    const rightCards = plan.placements.filter((placement) => placement.zone === 'right').sort((a, b) => a.priority - b.priority);
    expect(rightCards[0]?.id).toBe('failures');
    expect(['L', 'XL']).toContain(rightCards[0]?.size);
  });

  it('same signals twice returns identical plan', () => {
    const a = generateLayoutPlan(baseSignals);
    const b = generateLayoutPlan(baseSignals);
    expect(a).toEqual(b);
  });

  it('hysteresis keeps dominant card stable for tiny deltas', () => {
    const first = generateLayoutPlan({ ...baseSignals, remindersDueToday: 2, updatedAt: 10_000 });
    const second = generateLayoutPlan(
      { ...baseSignals, remindersDueToday: 3, alertsCount: 2, updatedAt: 10_020 },
      first
    );

    const dominantFirst = first.placements.find((placement) => placement.zone === 'center' && placement.priority === 0)?.id;
    const dominantSecond = second.placements.find((placement) => placement.zone === 'center' && placement.priority === 0)?.id;
    expect(dominantSecond).toBe(dominantFirst);
  });
});
