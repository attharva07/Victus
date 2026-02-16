import type { VictusUIState } from '../types/victus-ui';

// Adapter boundary reserved for future backend/client schema mismatches.
export function adaptProviderState(input: VictusUIState): VictusUIState {
  return {
    ...input,
    dialogue: { messages: [...input.dialogue.messages] },
    contextGroups: {
      approvals: [...input.contextGroups.approvals],
      alerts: [...input.contextGroups.alerts],
      reminders: [...input.contextGroups.reminders],
      workflows: [...input.contextGroups.workflows],
      failures: [...input.contextGroups.failures]
    },
    timeline: {
      today: [...input.timeline.today],
      upcoming: [...input.timeline.upcoming],
      completed: [...input.timeline.completed]
    }
  };
}
