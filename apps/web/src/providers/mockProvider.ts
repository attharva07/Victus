import type { UIProvider } from './UIProvider';
import type { ApprovalDecision, CardId, VictusUIState, VictusCard } from '../types/victus-ui';

const now = Date.now();

const baseCards: VictusUIState['cards'] = ([
  ['dialogue', 'FOCUS', 'L', 'primary'],
  ['timeline', 'FOCUS', 'M', 'secondary'],
  ['healthPulse', 'FOCUS', 'M', 'secondary'],
  ['systemOverview', 'FOCUS', 'S', 'secondary'],
  ['worldTldr', 'FOCUS', 'S', 'tertiary'],
  ['workflowsBoard', 'FOCUS', 'M', 'secondary'],
  ['remindersPanel', 'FOCUS', 'M', 'secondary'],
  ['approvalsPanel', 'FOCUS', 'M', 'secondary'],
  ['failures', 'CONTEXT', 'M', 'primary'],
  ['approvals', 'CONTEXT', 'M', 'primary'],
  ['alerts', 'CONTEXT', 'M', 'secondary'],
  ['reminders', 'CONTEXT', 'M', 'secondary'],
  ['workflows', 'CONTEXT', 'M', 'secondary']
] as const).reduce((acc, [id, lane, size, role]) => {
  acc[id] = {
    id,
    lane,
    size,
    role,
    pinned: false,
    expanded: true,
    priority: { urgency: 40, confidenceWeight: 0.25 }
  } as VictusCard;
  return acc;
}, {} as Record<CardId, VictusCard>);

export const initialMockProviderState: VictusUIState = {
  cards: baseCards,
  contextGroups: {
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
    workflows: [{ id: 'w-1', title: 'Weekly planning synthesis', progress: 60, stepLabel: 'Step 3/5', resumable: true }]
  },
  dialogue: {
    messages: [{ id: 'd-system-seed', role: 'system', text: 'Victus is active. Issue a command when ready.', createdAt: now - 60_000 }]
  },
  timeline: {
    today: [{ id: 't-1', bucket: 'Today', label: 'Executor heartbeat stable', detail: 'Automation channels nominal.', createdAt: now - 120_000 }],
    upcoming: [{ id: 't-2', bucket: 'Upcoming', label: 'Team planning sync', detail: 'Agenda locked for tomorrow.', createdAt: now - 80_000 }],
    completed: [{ id: 't-3', bucket: 'Completed', label: 'Inbox triage complete', detail: '12 items processed.', createdAt: now - 200_000 }]
  },
  worldTldr: [
    'Cloud costs are flat week-over-week.',
    'No critical CVEs in active dependency graph.',
    'User workload is elevated; bias toward fewer context switches.'
  ],
  bottomStrip: { mode: 'adaptive', planner: 'listening', executor: 'ready', domain: 'automation', confidence: 78 },
  lastUserInputAt: 0
};

const event = (label: string, detail: string, bucket: 'Today' | 'Upcoming' | 'Completed' = 'Today') => ({
  id: `timeline-${Date.now()}-${Math.random().toString(16).slice(2)}`,
  label,
  detail,
  bucket,
  createdAt: Date.now()
});

let state: VictusUIState = structuredClone(initialMockProviderState);

const cloneState = () => structuredClone(state);

export function resetMockProviderState() {
  state = structuredClone(initialMockProviderState);
}

export const mockProvider: UIProvider = {
  async getState() {
    return cloneState();
  },
  async decideApproval(id: string, decision: ApprovalDecision) {
    const target = state.contextGroups.approvals.find((item) => item.id === id);
    if (!target) return cloneState();
    state.contextGroups.approvals = state.contextGroups.approvals.filter((item) => item.id !== id);
    state.timeline.today = [event(`Approval resolved: ${target.title} (${decision})`, `Approval ${decision} by operator.`), ...state.timeline.today];
    return cloneState();
  },
  async submitCommand(text: string) {
    const clean = text.trim();
    if (!clean) return cloneState();
    const stamp = Date.now();
    state.lastUserInputAt = stamp;
    state.dialogue.messages = [
      ...state.dialogue.messages,
      { id: `d-user-${stamp}`, role: 'user', text: clean, createdAt: stamp },
      { id: `d-system-${stamp}`, role: 'system', text: `Acknowledged: ${clean}`, createdAt: stamp + 1 }
    ];
    return cloneState();
  },
  async ackAlert(id: string) {
    state.contextGroups.alerts = state.contextGroups.alerts.filter((item) => item.id !== id);
    return cloneState();
  },
  async markReminderDone(id: string) {
    const target = state.contextGroups.reminders.find((item) => item.id === id);
    if (!target) return cloneState();
    state.contextGroups.reminders = state.contextGroups.reminders.filter((item) => item.id !== id);
    state.timeline.today = [event(`Reminder completed: ${target.title}`, 'Reminder marked done from Focus lane.'), ...state.timeline.today];
    return cloneState();
  },
  async resumeWorkflow(id: string) {
    state.contextGroups.workflows = state.contextGroups.workflows.map((item) =>
      item.id === id ? { ...item, stepLabel: 'Resumed', progress: Math.min(100, item.progress + 10) } : item
    );
    return cloneState();
  }
};
