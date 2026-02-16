import type { LayoutSignals } from './signals';

export function getInitialSignals(): LayoutSignals {
  return {
    remindersCount: 2,
    remindersDueToday: 1,
    alertsCount: 1,
    alertsSeverity: 'low',
    failuresCount: 0,
    failuresSeverity: 'none',
    approvalsPending: 1,
    workflowsActive: 2,
    confidence: 'stable',
    confidenceScore: 82,
    dialogueOpen: false,
    focusMode: 'default',
    updatedAt: 1_000
  };
}

export function simulateUpdate(prev: LayoutSignals): LayoutSignals {
  const phase = Math.floor(prev.updatedAt / 1_000) % 4;

  if (phase === 0) {
    return {
      ...prev,
      failuresCount: 2,
      failuresSeverity: 'high',
      alertsCount: 2,
      alertsSeverity: 'medium',
      approvalsPending: prev.approvalsPending + 1,
      confidence: 'drifting',
      confidenceScore: 56,
      focusMode: 'review',
      updatedAt: prev.updatedAt + 1_000
    };
  }

  if (phase === 1) {
    return {
      ...prev,
      failuresCount: 3,
      failuresSeverity: 'critical',
      approvalsPending: prev.approvalsPending + 1,
      remindersDueToday: Math.min(prev.remindersDueToday + 1, prev.remindersCount + 1),
      confidence: 'unstable',
      confidenceScore: 28,
      focusMode: 'recovery',
      updatedAt: prev.updatedAt + 1_000
    };
  }

  if (phase === 2) {
    return {
      ...prev,
      failuresCount: 1,
      failuresSeverity: 'medium',
      alertsCount: 1,
      alertsSeverity: 'low',
      approvalsPending: Math.max(0, prev.approvalsPending - 1),
      confidence: 'drifting',
      confidenceScore: 48,
      focusMode: 'focus',
      updatedAt: prev.updatedAt + 1_000
    };
  }

  return {
    ...prev,
    failuresCount: 0,
    failuresSeverity: 'none',
    remindersDueToday: 1,
    approvalsPending: 1,
    alertsCount: 1,
    alertsSeverity: 'low',
    confidence: 'stable',
    confidenceScore: 86,
    focusMode: 'default',
    updatedAt: prev.updatedAt + 1_000
  };
}
