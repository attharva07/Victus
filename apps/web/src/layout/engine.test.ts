import { describe, expect, it } from 'vitest';
import { generateLayoutPlan } from './engine';
import type { LayoutSignals } from './signals';

const baseSignals: LayoutSignals = {
  remindersCount: 1,
  alertsCount: 1,
  alertsSeverity: 'low',
  failuresCount: 0,
  failuresSeverity: 'none',
  approvalsPending: 0,
  workflowsActive: 1,
  confidence: 'stable',
  dialogueOpen: false,
  focusMode: 'default',
  updatedAt: 1000
};

describe('layout engine phase 4B', () => {
  it('dialogueOpen -> dialogue card XL full width and active id', () => {
    const plan = generateLayoutPlan({ ...baseSignals, dialogueOpen: true });

    expect(plan.activeCardId).toBe('dialogue');
    expect(plan.placements).toEqual([
      expect.objectContaining({ id: 'dialogue', size: 'XL', colSpan: 2, zone: 'center' })
    ]);
  });

  it('high severity failures are at least large', () => {
    const plan = generateLayoutPlan({ ...baseSignals, failuresCount: 2, failuresSeverity: 'high', confidence: 'unstable' });
    const failures = plan.placements.find((placement) => placement.id === 'failures');

    expect(failures).toBeDefined();
    expect(['L', 'XL']).toContain(failures?.size);
  });

  it('approvals pending keeps approvals visible at least S', () => {
    const plan = generateLayoutPlan({ ...baseSignals, approvalsPending: 1 });
    const approvals = plan.placements.find((placement) => placement.id === 'approvals');

    expect(approvals).toBeDefined();
    expect(['S', 'M', 'L', 'XL']).toContain(approvals?.size);
  });

  it('chooses P2 for mixed active signals', () => {
    const plan = generateLayoutPlan({
      ...baseSignals,
      remindersCount: 2,
      alertsCount: 2,
      alertsSeverity: 'medium',
      failuresCount: 1,
      failuresSeverity: 'high',
      approvalsPending: 1,
      workflowsActive: 2
    });

    expect(plan.preset).toBe('P2');
  });

  it('is deterministic for same signals', () => {
    const a = generateLayoutPlan(baseSignals);
    const b = generateLayoutPlan(baseSignals);

    expect(a).toEqual(b);
  });
});
