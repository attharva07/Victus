import type { LayoutSignals } from './signals';

const scenarios: Omit<LayoutSignals, 'updatedAt' | 'dialogueOpen'>[] = [
  {
    remindersCount: 1,
    alertsCount: 1,
    alertsSeverity: 'low',
    failuresCount: 0,
    failuresSeverity: 'none',
    approvalsPending: 1,
    workflowsActive: 2,
    confidence: 'stable',
    focusMode: 'default'
  },
  {
    remindersCount: 3,
    alertsCount: 2,
    alertsSeverity: 'medium',
    failuresCount: 1,
    failuresSeverity: 'high',
    approvalsPending: 2,
    workflowsActive: 2,
    confidence: 'drifting',
    focusMode: 'review'
  },
  {
    remindersCount: 2,
    alertsCount: 3,
    alertsSeverity: 'high',
    failuresCount: 2,
    failuresSeverity: 'critical',
    approvalsPending: 1,
    workflowsActive: 1,
    confidence: 'unstable',
    focusMode: 'recovery'
  }
];

export function getInitialSignals(): LayoutSignals {
  return {
    ...scenarios[0],
    dialogueOpen: false,
    updatedAt: Date.now()
  };
}

export function simulateUpdate(prev: LayoutSignals): LayoutSignals {
  const nextIdx = (Math.floor(prev.updatedAt / 1000) + 1) % scenarios.length;

  return {
    ...scenarios[nextIdx],
    dialogueOpen: prev.dialogueOpen,
    updatedAt: prev.updatedAt + 1000
  };
}
