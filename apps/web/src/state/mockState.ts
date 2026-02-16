export type Severity = 'info' | 'warning' | 'critical';

export type FailureItem = { id: string; title: string; severity: Severity; ageMinutes: number };
export type ApprovalItem = { id: string; title: string; detail: string; requestedBy: string };
export type AlertItem = { id: string; title: string; detail: string };
export type ReminderItem = { id: string; title: string; due: string; urgency: 'low' | 'medium' | 'high' };
export type WorkflowItem = { id: string; title: string; progress: number; stepLabel: string };
export type DialogueMessage = { id: string; role: 'user' | 'system'; text: string; createdAt: number };
export type TimelineEvent = {
  id: string;
  bucket: 'Today' | 'Upcoming' | 'Completed';
  label: string;
  detail: string;
  createdAt: number;
};

export type MockUiState = {
  failures: FailureItem[];
  approvals: ApprovalItem[];
  alerts: AlertItem[];
  reminders: ReminderItem[];
  workflows: WorkflowItem[];
  dialogue: DialogueMessage[];
  timeline: TimelineEvent[];
  worldTldr: string[];
  confidence: number;
  lastUserInputAt: number;
};

const now = Date.now();

export const initialMockState: MockUiState = {
  failures: [{ id: 'f-1', title: 'Orchestrator retry exhausted', severity: 'warning', ageMinutes: 18 }],
  approvals: [{ id: 'ap-1', title: 'Filesystem tool scope adjustment', detail: 'Grant wider read/write scope for migration script.', requestedBy: 'Executor' }],
  alerts: [
    { id: 'al-1', title: 'Memory latency drift', detail: '95th percentile latency is up 12%.' },
    { id: 'al-2', title: 'Finance feed delayed', detail: 'Last import is 11m behind schedule.' }
  ],
  reminders: [
    { id: 'r-1', title: 'Approve onboarding policy edits', due: 'Today 2:00 PM', urgency: 'high' },
    { id: 'r-2', title: 'Share architecture notes', due: 'Today 4:00 PM', urgency: 'medium' }
  ],
  workflows: [{ id: 'w-1', title: 'Weekly planning synthesis', progress: 60, stepLabel: 'Step 3/5' }],
  dialogue: [{ id: 'd-system-seed', role: 'system', text: 'Victus is active. Issue a command when ready.', createdAt: now - 60_000 }],
  timeline: [
    { id: 't-1', bucket: 'Today', label: 'Executor heartbeat stable', detail: 'Automation channels nominal.', createdAt: now - 120_000 },
    { id: 't-2', bucket: 'Upcoming', label: 'Team planning sync', detail: 'Agenda locked for tomorrow.', createdAt: now - 80_000 },
    { id: 't-3', bucket: 'Completed', label: 'Inbox triage complete', detail: '12 items processed.', createdAt: now - 200_000 }
  ],
  worldTldr: [
    'Cloud costs are flat week-over-week.',
    'No critical CVEs in active dependency graph.',
    'User workload is elevated; bias toward fewer context switches.'
  ],
  confidence: 78,
  lastUserInputAt: 0
};

const timelineEvent = (label: string, detail: string, bucket: TimelineEvent['bucket'] = 'Today'): TimelineEvent => ({
  id: `timeline-${Date.now()}-${Math.random().toString(16).slice(2)}`,
  bucket,
  label,
  detail,
  createdAt: Date.now()
});

export function applyApprovalDecision(state: MockUiState, approvalId: string, decision: 'approved' | 'denied'): MockUiState {
  const target = state.approvals.find((item) => item.id === approvalId);
  if (!target) return state;

  return {
    ...state,
    approvals: state.approvals.filter((item) => item.id !== approvalId),
    timeline: [timelineEvent(`Approval resolved: ${target.title} (${decision})`, `Approval ${decision} by operator.`), ...state.timeline]
  };
}

export function markReminderDone(state: MockUiState, reminderId: string): MockUiState {
  const target = state.reminders.find((item) => item.id === reminderId);
  if (!target) return state;

  return {
    ...state,
    reminders: state.reminders.filter((item) => item.id !== reminderId),
    timeline: [timelineEvent(`Reminder completed: ${target.title}`, 'Reminder marked done from Focus lane.'), ...state.timeline]
  };
}

export function submitCommand(state: MockUiState, text: string): MockUiState {
  const clean = text.trim();
  if (!clean) return state;
  const stamp = Date.now();

  return {
    ...state,
    lastUserInputAt: stamp,
    dialogue: [
      ...state.dialogue,
      { id: `d-user-${stamp}`, role: 'user', text: clean, createdAt: stamp },
      { id: `d-system-${stamp}`, role: 'system', text: `Acknowledged: ${clean}`, createdAt: stamp + 1 }
    ]
  };
}
