export type Severity = 'none' | 'low' | 'medium' | 'high' | 'critical';

export type ConfidenceStability = 'stable' | 'drifting' | 'unstable';

export type LayoutSignals = {
  remindersCount: number;
  remindersDueToday: number;
  approvalsPending: number;
  alertsCount: number;
  alertsSeverity: Severity;
  failuresCount: number;
  failuresSeverity: Severity;
  workflowsActive: number;
  dialogueOpen: boolean;
  userTyping: boolean;
  confidenceScore: number;
  confidenceStability: ConfidenceStability;
};
