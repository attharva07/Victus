import { describe, expect, it } from 'vitest';
import { generateLayoutPlan } from './engine';
import type { LayoutSignals } from './signals';

const baseSignals: LayoutSignals = {
  remindersCount: 2,
  remindersDueToday: 1,
  approvalsPending: 1,
  alertsCount: 1,
  alertsSeverity: 'low',
  failuresCount: 0,
  failuresSeverity: 'none',
  workflowsActive: 1,
  dialogueOpen: false,
  userTyping: false,
  confidenceScore: 82,
  confidenceStability: 'stable'
};

describe('phase 4B lane layout engine', () => {
  it('same signals produce deterministic card ordering and preset', () => {
    const a = generateLayoutPlan(baseSignals);
    const b = generateLayoutPlan(baseSignals);

    expect(a.dominantCardId).toBe(b.dominantCardId);
    expect(a.supportingCardIds).toEqual(b.supportingCardIds);
    expect(a.compactCardIds).toEqual(b.compactCardIds);
    expect(a.rightContextCardIds).toEqual(b.rightContextCardIds);
    expect(a.preset).toBe(b.preset);
  });

  it('dialogueOpen drives dominant dialogue unless confidence drops below 25', () => {
    const dialoguePlan = generateLayoutPlan({ ...baseSignals, dialogueOpen: true, confidenceScore: 70 });
    const lowConfidencePlan = generateLayoutPlan({ ...baseSignals, dialogueOpen: true, confidenceScore: 20 });

    expect(dialoguePlan.dominantCardId).toBe('dialogue');
    expect(lowConfidencePlan.dominantCardId).toBe('failures');
  });

  it('critical failures always dominate', () => {
    const plan = generateLayoutPlan({
      ...baseSignals,
      failuresCount: 3,
      failuresSeverity: 'critical',
      dialogueOpen: true,
      confidenceScore: 80
    });

    expect(plan.dominantCardId).toBe('failures');
    expect(plan.preset).toBe('STABILIZE');
  });

  it('maps dominant/supporting/compact cards into focus/peek/chip states', () => {
    const plan = generateLayoutPlan({ ...baseSignals, dialogueOpen: true, remindersCount: 5, remindersDueToday: 2 });

    expect(plan.cardStates[plan.dominantCardId]).toBe('focus');
    plan.supportingCardIds.forEach((id) => expect(plan.cardStates[id]).toBe('peek'));
    plan.compactCardIds.forEach((id) => expect(plan.cardStates[id]).toBe('chip'));
  });
});
