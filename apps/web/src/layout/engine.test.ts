import { describe, expect, it } from 'vitest';
import { buildAdaptiveLayoutPlan, mockLayoutSignals } from './engine';

describe('hybrid adaptive layout engine', () => {
  it('selects recovery preset deterministically for critical failures', () => {
    const signals = mockLayoutSignals({ failuresCount: 2, failuresSeverity: 'critical', updatedAt: 123 });
    const plan = buildAdaptiveLayoutPlan(signals);

    expect(plan.preset).toBe('P5');
    expect(plan.splitColumns).toBe('rightFocus');
    expect(plan.activeCardId).toBe('failures');
    expect(plan.generatedAt).toBe(123);
    expect(plan.placements.find((placement) => placement.id === 'failures')?.size).toBe('L');
  });

  it('prioritizes review layout when approvals and dialogue are active', () => {
    const plan = buildAdaptiveLayoutPlan(
      mockLayoutSignals({
        dialogueOpen: true,
        approvalsPending: 2,
        workflowsActive: 1,
        focusMode: 'review'
      })
    );

    expect(plan.preset).toBe('P2');
    expect(plan.activeCardId).toBe('approvals');
    const rightOrder = plan.placements.filter((placement) => placement.zone === 'right').map((placement) => placement.id);
    expect(rightOrder.slice(0, 2)).toEqual(['approvals', 'workflows']);
  });

  it('keeps identical outputs for identical signals', () => {
    const signals = mockLayoutSignals({ alertsCount: 2, alertsSeverity: 'high', confidence: 'drifting', updatedAt: 777 });
    const first = buildAdaptiveLayoutPlan(signals);
    const second = buildAdaptiveLayoutPlan(signals);

    expect(second).toEqual(first);
  });
});
