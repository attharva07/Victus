export type VictusItemKind = 'event' | 'reminder' | 'alert' | 'approval' | 'workflow' | 'failure';
export type VictusCardKind = 'reminders' | 'alerts' | 'approvals' | 'workflows' | 'failures';
export type ItemStatus = 'active' | 'completed' | 'dismissed' | 'resolved';
export type EventType = 'user' | 'system';

export type VictusItem = {
  id: string;
  kind: VictusItemKind;
  title: string;
  detail: string;
  type: EventType;
  timeLabel: string;
  source: string;
  domain: string;
  createdAt: string;
  updatedAt: string;
  status: ItemStatus;
  acknowledged?: boolean;
  muted?: boolean;
  pinned?: boolean;
  snoozedUntil?: string;
  approvalState?: 'pending' | 'approved' | 'denied';
  workflowState?: 'active' | 'paused';
  resolved?: boolean;
};

export type VictusCard = {
  kind: VictusCardKind;
  title: string;
  collapsed: boolean;
  itemIds: string[];
};

export type VictusState = {
  timeline: {
    today: string[];
    upcoming: string[];
    completed: string[];
  };
  contextCards: VictusCard[];
  items: Record<string, VictusItem>;
};

const nowStamp = '2026-02-16 09:30';

const eventItems: VictusItem[] = [
  {
    id: 't1',
    kind: 'event',
    title: 'Review deployment checklist',
    detail: 'Confirm production gating and change notes before noon sync.',
    timeLabel: '10:00 AM',
    type: 'user',
    source: 'Planner',
    domain: 'Operations',
    createdAt: '2026-02-16 08:45',
    updatedAt: nowStamp,
    status: 'active'
  },
  {
    id: 't2',
    kind: 'event',
    title: 'Draft Q2 planning prompts',
    detail: 'Prepare structured prompt set for roadmap decomposition.',
    timeLabel: '11:30 AM',
    type: 'user',
    source: 'Workspace',
    domain: 'Strategy',
    createdAt: '2026-02-16 08:50',
    updatedAt: nowStamp,
    status: 'active'
  },
  {
    id: 't3',
    kind: 'event',
    title: 'Confidence drift monitor sweep',
    detail: 'System analyzer detected mild deviation in memory retrieval confidence.',
    timeLabel: '1:15 PM',
    type: 'system',
    source: 'System Analyzer',
    domain: 'Memory',
    createdAt: '2026-02-16 09:00',
    updatedAt: nowStamp,
    status: 'active'
  },
  {
    id: 't4',
    kind: 'event',
    title: 'Workflow reconciler checkpoint',
    detail: 'Executor checkpoint passed 7/8 tasks; one pending approval remains.',
    timeLabel: '3:20 PM',
    type: 'system',
    source: 'Executor',
    domain: 'Automation',
    createdAt: '2026-02-16 09:10',
    updatedAt: nowStamp,
    status: 'active'
  },
  {
    id: 'u1',
    kind: 'event',
    title: 'Team planning sync',
    detail: 'Agenda locked and context bundle prepared.',
    timeLabel: 'Tomorrow',
    type: 'user',
    source: 'Planner',
    domain: 'Team Ops',
    createdAt: '2026-02-16 07:40',
    updatedAt: nowStamp,
    status: 'active'
  },
  {
    id: 'u2',
    kind: 'event',
    title: 'Finance digest compile',
    detail: 'Auto-summary for weekly cash movement review.',
    timeLabel: 'Thu 9:00 AM',
    type: 'system',
    source: 'Finance Agent',
    domain: 'Finance',
    createdAt: '2026-02-16 07:41',
    updatedAt: nowStamp,
    status: 'active'
  },
  {
    id: 'u3',
    kind: 'event',
    title: 'Memory retention review',
    detail: 'Policy tune proposal generated for review.',
    timeLabel: 'Fri',
    type: 'system',
    source: 'Memory Orchestrator',
    domain: 'Memory',
    createdAt: '2026-02-16 07:43',
    updatedAt: nowStamp,
    status: 'active'
  },
  {
    id: 'u4',
    kind: 'event',
    title: 'Goal reprioritization window',
    detail: 'Run quick prioritization pass with updated blockers.',
    timeLabel: 'Fri 3:00 PM',
    type: 'user',
    source: 'Planner',
    domain: 'Strategy',
    createdAt: '2026-02-16 07:44',
    updatedAt: nowStamp,
    status: 'active'
  },
  {
    id: 'c1',
    kind: 'event',
    title: 'Inbox triage complete',
    detail: '12 items processed with tags and follow-ups.',
    timeLabel: '8:45 AM',
    type: 'user',
    source: 'Inbox',
    domain: 'Comms',
    createdAt: '2026-02-16 08:45',
    updatedAt: nowStamp,
    status: 'completed'
  },
  {
    id: 'c2',
    kind: 'event',
    title: 'Failure queue normalized',
    detail: 'Resolved stale retries in orchestration loop.',
    timeLabel: '9:10 AM',
    type: 'system',
    source: 'Workflow Monitor',
    domain: 'Automation',
    createdAt: '2026-02-16 08:52',
    updatedAt: nowStamp,
    status: 'completed'
  },
  {
    id: 'c3',
    kind: 'event',
    title: 'Domain health heartbeat',
    detail: 'All monitored domains returned healthy.',
    timeLabel: '9:40 AM',
    type: 'system',
    source: 'System Health',
    domain: 'Infra',
    createdAt: '2026-02-16 08:59',
    updatedAt: nowStamp,
    status: 'completed'
  }
];

const contextItems: VictusItem[] = [
  {
    id: 'r1',
    kind: 'reminder',
    title: 'Approve onboarding policy edits',
    detail: 'Policy doc edits are waiting for your confirmation.',
    timeLabel: 'due today',
    type: 'user',
    source: 'Policy Assistant',
    domain: 'Ops',
    createdAt: '2026-02-16 07:10',
    updatedAt: nowStamp,
    status: 'active'
  },
  {
    id: 'r2',
    kind: 'reminder',
    title: 'Send architecture notes to team',
    detail: 'Share latest architecture notes in team channel.',
    timeLabel: '2h left',
    type: 'user',
    source: 'Workspace',
    domain: 'Engineering',
    createdAt: '2026-02-16 07:20',
    updatedAt: nowStamp,
    status: 'active'
  },
  {
    id: 'a1',
    kind: 'alert',
    title: 'Memory latency above baseline',
    detail: 'Observed mild latency increase for memory queries.',
    timeLabel: 'minor',
    type: 'system',
    source: 'Telemetry',
    domain: 'Memory',
    createdAt: '2026-02-16 09:00',
    updatedAt: nowStamp,
    status: 'active'
  },
  {
    id: 'a2',
    kind: 'alert',
    title: 'Finance feed delayed',
    detail: 'Finance ingestion job is delayed from expected schedule.',
    timeLabel: 'watching',
    type: 'system',
    source: 'Finance Agent',
    domain: 'Finance',
    createdAt: '2026-02-16 09:05',
    updatedAt: nowStamp,
    status: 'active'
  },
  {
    id: 'p1',
    kind: 'approval',
    title: 'Filesystem tool scope adjustment',
    detail: 'Executor requests broader filesystem scope for migration script.',
    timeLabel: 'requires review',
    type: 'system',
    source: 'Executor',
    domain: 'Automation',
    createdAt: '2026-02-16 09:15',
    updatedAt: nowStamp,
    status: 'active',
    approvalState: 'pending'
  },
  {
    id: 'w1',
    kind: 'workflow',
    title: 'Weekly planning synthesis',
    detail: 'Generating combined planning summary from all domains.',
    timeLabel: 'step 3/5',
    type: 'system',
    source: 'Workflow Engine',
    domain: 'Planning',
    createdAt: '2026-02-16 08:35',
    updatedAt: nowStamp,
    status: 'active',
    workflowState: 'active'
  },
  {
    id: 'w2',
    kind: 'workflow',
    title: 'Contextual memory digest',
    detail: 'Building updated memory digest for the afternoon session.',
    timeLabel: 'step 1/4',
    type: 'system',
    source: 'Memory Orchestrator',
    domain: 'Memory',
    createdAt: '2026-02-16 08:38',
    updatedAt: nowStamp,
    status: 'active',
    workflowState: 'paused'
  },
  {
    id: 'f1',
    kind: 'failure',
    title: 'Orchestrator retry exhausted',
    detail: 'Retry budget exhausted for a background orchestrator task.',
    timeLabel: 'open 18m',
    type: 'system',
    source: 'Workflow Monitor',
    domain: 'Automation',
    createdAt: '2026-02-16 09:12',
    updatedAt: nowStamp,
    status: 'active'
  }
];

const worldTldr = [
  'Macro update: cloud costs trending flat this week; no immediate action needed.',
  'Security brief: no new critical advisories affecting active stack.',
  'Signals: user workload elevated; suggest lower context-switch operations this afternoon.'
];

const items = [...eventItems, ...contextItems].reduce<Record<string, VictusItem>>((acc, item) => {
  acc[item.id] = item;
  return acc;
}, {});

export const initialVictusState: VictusState = {
  timeline: {
    today: ['t1', 't2', 't3', 't4'],
    upcoming: ['u1', 'u2', 'u3', 'u4'],
    completed: ['c1', 'c2', 'c3']
  },
  contextCards: [
    { kind: 'reminders', title: 'Reminders', collapsed: false, itemIds: ['r1', 'r2'] },
    { kind: 'alerts', title: 'Alerts', collapsed: false, itemIds: ['a1', 'a2'] },
    { kind: 'approvals', title: 'Pending Approvals', collapsed: false, itemIds: ['p1'] },
    { kind: 'workflows', title: 'Active Workflows', collapsed: false, itemIds: ['w1', 'w2'] },
    { kind: 'failures', title: 'Unresolved Failures', collapsed: false, itemIds: ['f1'] }
  ],
  items
};

export const worldTldrEntries = worldTldr;

const stamp = () => new Date().toLocaleString();

const patchItem = (state: VictusState, id: string, patch: Partial<VictusItem>): VictusState => {
  const item = state.items[id];
  if (!item) {
    return state;
  }

  return {
    ...state,
    items: {
      ...state.items,
      [id]: { ...item, ...patch, updatedAt: stamp() }
    }
  };
};

const removeFromLists = (list: string[], id: string) => list.filter((entry) => entry !== id);

const appendSystemTimelineEvent = (state: VictusState, title: string, detail: string): VictusState => {
  const timestamp = Date.now();
  const eventId = `sys-${timestamp}`;
  const event: VictusItem = {
    id: eventId,
    kind: 'event',
    title,
    detail,
    timeLabel: 'Just now',
    type: 'system',
    source: 'Context Stack',
    domain: 'Automation',
    createdAt: stamp(),
    updatedAt: stamp(),
    status: 'active'
  };

  return {
    ...state,
    items: {
      ...state.items,
      [eventId]: event
    },
    timeline: {
      ...state.timeline,
      today: [eventId, ...state.timeline.today]
    }
  };
};

export const markDone = (state: VictusState, id: string): VictusState => {
  if (!state.items[id]) return state;

  const next = patchItem(state, id, { status: 'completed' });
  return {
    ...next,
    timeline: {
      today: removeFromLists(next.timeline.today, id),
      upcoming: removeFromLists(next.timeline.upcoming, id),
      completed: next.timeline.completed.includes(id) ? next.timeline.completed : [id, ...next.timeline.completed]
    },
    contextCards: next.contextCards.map((card) => ({ ...card, itemIds: removeFromLists(card.itemIds, id) }))
  };
};

export const dismiss = (state: VictusState, id: string): VictusState => {
  const next = patchItem(state, id, { status: 'dismissed' });
  return {
    ...next,
    timeline: {
      today: removeFromLists(next.timeline.today, id),
      upcoming: removeFromLists(next.timeline.upcoming, id),
      completed: removeFromLists(next.timeline.completed, id)
    },
    contextCards: next.contextCards.map((card) => ({ ...card, itemIds: removeFromLists(card.itemIds, id) }))
  };
};

export const acknowledge = (state: VictusState, id: string): VictusState => patchItem(state, id, { acknowledged: true });

export const pinToReminders = (state: VictusState, id: string): VictusState => {
  const item = state.items[id];
  if (!item) return state;

  const reminderId = `rem-${id}`;
  const reminderItem: VictusItem = {
    id: reminderId,
    kind: 'reminder',
    title: `Reminder: ${item.title}`,
    detail: `Pinned from timeline: ${item.detail}`,
    timeLabel: 'pinned',
    type: 'user',
    source: 'Pinned',
    domain: item.domain,
    createdAt: stamp(),
    updatedAt: stamp(),
    status: 'active'
  };

  return {
    ...patchItem(state, id, { pinned: true }),
    items: {
      ...state.items,
      [id]: { ...state.items[id], pinned: true, updatedAt: stamp() },
      ...(state.items[reminderId] ? {} : { [reminderId]: reminderItem })
    },
    contextCards: state.contextCards.map((card) =>
      card.kind === 'reminders' && !card.itemIds.includes(reminderId) ? { ...card, itemIds: [reminderId, ...card.itemIds] } : card
    )
  };
};

export const snooze = (state: VictusState, id: string): VictusState => patchItem(state, id, { snoozedUntil: 'Tomorrow 9:00 AM' });

const resolveApproval = (state: VictusState, id: string, decision: 'approved' | 'denied'): VictusState => {
  const approval = state.items[id];
  if (!approval) return state;

  const withDecision = patchItem(state, id, { approvalState: decision, status: 'resolved' });
  const trimmed = {
    ...withDecision,
    contextCards: withDecision.contextCards.map((card) =>
      card.kind === 'approvals' ? { ...card, itemIds: removeFromLists(card.itemIds, id) } : card
    )
  };

  return appendSystemTimelineEvent(
    trimmed,
    `Approval resolved: ${approval.title} (${decision})`,
    `Approval ${approval.title} was ${decision} from Context Stack.`
  );
};

export const approve = (state: VictusState, id: string): VictusState => resolveApproval(state, id, 'approved');

export const deny = (state: VictusState, id: string): VictusState => resolveApproval(state, id, 'denied');

export const toggleWorkflow = (state: VictusState, id: string): VictusState => {
  const workflow = state.items[id];
  if (!workflow) return state;

  const next = workflow.workflowState === 'paused' ? 'active' : 'paused';
  return patchItem(state, id, { workflowState: next });
};

export const resolveFailure = (state: VictusState, id: string): VictusState => {
  const next = patchItem(state, id, { status: 'resolved', resolved: true });
  return {
    ...next,
    contextCards: next.contextCards.map((card) =>
      card.kind === 'failures' ? { ...card, itemIds: removeFromLists(card.itemIds, id) } : card
    )
  };
};

export const mute = (state: VictusState, id: string): VictusState => patchItem(state, id, { muted: true });

export const addCommandEvent = (state: VictusState, text: string): VictusState => {
  const clean = text.trim();
  if (!clean) return state;

  const timestamp = Date.now();
  const userId = `cmd-user-${timestamp}`;
  const systemId = `cmd-system-${timestamp}`;

  const userEvent: VictusItem = {
    id: userId,
    kind: 'event',
    title: `Command: ${clean}`,
    detail: 'Submitted from Command Dock.',
    timeLabel: 'Just now',
    type: 'user',
    source: 'Command Dock',
    domain: 'Workspace',
    createdAt: stamp(),
    updatedAt: stamp(),
    status: 'active'
  };

  const systemEvent: VictusItem = {
    id: systemId,
    kind: 'event',
    title: 'Queued by executor',
    detail: `Executor queued command "${clean}".`,
    timeLabel: 'Just now',
    type: 'system',
    source: 'Executor',
    domain: 'Automation',
    createdAt: stamp(),
    updatedAt: stamp(),
    status: 'active'
  };

  return {
    ...state,
    items: {
      ...state.items,
      [userId]: userEvent,
      [systemId]: systemEvent
    },
    timeline: {
      ...state.timeline,
      today: [userId, systemId, ...state.timeline.today]
    }
  };
};

export const toggleCard = (state: VictusState, kind: VictusCardKind): VictusState => ({
  ...state,
  contextCards: state.contextCards.map((card) => (card.kind === kind ? { ...card, collapsed: !card.collapsed } : card))
});
