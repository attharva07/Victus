import type { LayoutSignals } from './signals';

export function getInitialSignals(): LayoutSignals {
  return {
    remindersCount: 2,
    remindersDueToday: 1,
    approvalsPending: 1,
    alertsCount: 2,
    alertsSeverity: 'low',
    failuresCount: 1,
    failuresSeverity: 'none',
    workflowsActive: 2,
    dialogueOpen: false,
    userTyping: false,
    confidenceScore: 82,
    confidenceStability: 'stable'
  };
}

export function simulateUpdate(prev: LayoutSignals): LayoutSignals {
  const step = (prev.remindersCount + prev.approvalsPending + prev.failuresCount) % 3;

  if (step === 0) {
    return {
      ...prev,
      failuresCount: Math.max(prev.failuresCount, 2),
      failuresSeverity: 'high',
      approvalsPending: prev.approvalsPending + 1,
      alertsCount: prev.alertsCount + 1,
      alertsSeverity: 'medium',
      confidenceScore: Math.max(35, prev.confidenceScore - 18),
      confidenceStability: 'drifting',
      dialogueOpen: false,
      userTyping: false
    };
  }

  if (step === 1) {
    return {
      ...prev,
      failuresCount: prev.failuresCount + 1,
      failuresSeverity: 'critical',
      approvalsPending: prev.approvalsPending + 2,
      remindersDueToday: prev.remindersDueToday + 1,
      confidenceScore: Math.max(20, prev.confidenceScore - 25),
      confidenceStability: 'unstable',
      dialogueOpen: false,
      userTyping: false
    };
  }

  return {
    ...prev,
    failuresCount: Math.max(0, prev.failuresCount - 1),
    failuresSeverity: 'medium',
    approvalsPending: Math.max(1, prev.approvalsPending - 1),
    alertsCount: Math.max(1, prev.alertsCount - 1),
    alertsSeverity: 'low',
    confidenceScore: Math.min(95, prev.confidenceScore + 10),
    confidenceStability: 'drifting'
  };
}
