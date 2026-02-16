export type Severity = 'none' | 'low' | 'medium' | 'high' | 'critical';

export type ConfidenceStability = 'stable' | 'drifting' | 'unstable';

export type FocusMode = 'default' | 'focus' | 'review' | 'recovery';

export type LayoutSignals = {
  remindersCount: number;
  remindersDueToday: number;
  alertsCount: number;
  alertsSeverity: Severity;
  failuresCount: number;
  failuresSeverity: Severity;
  approvalsPending: number;
  workflowsActive: number;

  confidence: ConfidenceStability;
  confidenceScore: number;

  dialogueOpen: boolean;
  focusMode: FocusMode;
  updatedAt: number;
};
