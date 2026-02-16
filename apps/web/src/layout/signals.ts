export type Severity = 'none' | 'low' | 'medium' | 'high' | 'critical';

export type ConfidenceStability = 'stable' | 'drifting' | 'unstable';

export type FocusMode = 'default' | 'focus' | 'review' | 'recovery';

export type LayoutSignals = {
  remindersCount: number;
  alertsCount: number;
  alertsSeverity: Severity;
  failuresCount: number;
  failuresSeverity: Severity;
  approvalsPending: number;
  workflowsActive: number;
  confidence: ConfidenceStability;
  dialogueOpen: boolean;
  focusMode: FocusMode;
  updatedAt: number;
};
