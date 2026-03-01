import type { ApprovalDecision, VictusUIState } from '../types/victus-ui';

export interface UIProvider {
  getState(): Promise<VictusUIState>;
  decideApproval(id: string, decision: ApprovalDecision): Promise<VictusUIState>;
  submitCommand(text: string): Promise<VictusUIState>;
  ackAlert(id: string): Promise<VictusUIState>;
  markReminderDone(id: string): Promise<VictusUIState>;
  resumeWorkflow(id: string): Promise<VictusUIState>;
}
