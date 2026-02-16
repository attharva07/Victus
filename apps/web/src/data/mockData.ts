export type EventType = 'user' | 'system';

export type TimelineEvent = {
  id: string;
  title: string;
  detail: string;
  timeLabel: string;
  type: EventType;
};

export type ContextItem = { id: string; label: string; meta?: string };

export type ContextCardData = {
  id: string;
  title: string;
  items: ContextItem[];
};

export const todayEvents: TimelineEvent[] = [
  {
    id: 't1',
    title: 'Review deployment checklist',
    detail: 'Confirm production gating and change notes before noon sync.',
    timeLabel: '10:00 AM',
    type: 'user'
  },
  {
    id: 't2',
    title: 'Draft Q2 planning prompts',
    detail: 'Prepare structured prompt set for roadmap decomposition.',
    timeLabel: '11:30 AM',
    type: 'user'
  },
  {
    id: 't3',
    title: 'Confidence drift monitor sweep',
    detail: 'System analyzer detected mild deviation in memory retrieval confidence.',
    timeLabel: '1:15 PM',
    type: 'system'
  },
  {
    id: 't4',
    title: 'Workflow reconciler checkpoint',
    detail: 'Executor checkpoint passed 7/8 tasks; one pending approval remains.',
    timeLabel: '3:20 PM',
    type: 'system'
  }
];

export const upcomingEvents: TimelineEvent[] = [
  { id: 'u1', title: 'Team planning sync', detail: 'Agenda locked and context bundle prepared.', timeLabel: 'Tomorrow', type: 'user' },
  { id: 'u2', title: 'Finance digest compile', detail: 'Auto-summary for weekly cash movement review.', timeLabel: 'Thu 9:00 AM', type: 'system' },
  { id: 'u3', title: 'Memory retention review', detail: 'Policy tune proposal generated for review.', timeLabel: 'Fri', type: 'system' },
  { id: 'u4', title: 'Goal reprioritization window', detail: 'Run quick prioritization pass with updated blockers.', timeLabel: 'Fri 3:00 PM', type: 'user' }
];

export const completedEvents: TimelineEvent[] = [
  { id: 'c1', title: 'Inbox triage complete', detail: '12 items processed with tags and follow-ups.', timeLabel: '8:45 AM', type: 'user' },
  { id: 'c2', title: 'Failure queue normalized', detail: 'Resolved stale retries in orchestration loop.', timeLabel: '9:10 AM', type: 'system' },
  { id: 'c3', title: 'Domain health heartbeat', detail: 'All monitored domains returned healthy.', timeLabel: '9:40 AM', type: 'system' }
];

export const worldTldr = [
  'Macro update: cloud costs trending flat this week; no immediate action needed.',
  'Security brief: no new critical advisories affecting active stack.',
  'Signals: user workload elevated; suggest lower context-switch operations this afternoon.'
];

export const contextCards: ContextCardData[] = [
  {
    id: 'reminders',
    title: 'Reminders',
    items: [
      { id: 'r1', label: 'Approve onboarding policy edits', meta: 'due today' },
      { id: 'r2', label: 'Send architecture notes to team', meta: '2h left' }
    ]
  },
  {
    id: 'alerts',
    title: 'Alerts',
    items: [
      { id: 'a1', label: 'Memory latency above baseline', meta: 'minor' },
      { id: 'a2', label: 'Finance feed delayed', meta: 'watching' }
    ]
  },
  {
    id: 'approvals',
    title: 'Pending Approvals',
    items: [
      { id: 'p1', label: 'Filesystem tool scope adjustment', meta: 'requires review' }
    ]
  },
  {
    id: 'workflows',
    title: 'Active Workflows',
    items: [
      { id: 'w1', label: 'Weekly planning synthesis', meta: 'step 3/5' },
      { id: 'w2', label: 'Contextual memory digest', meta: 'step 1/4' }
    ]
  },
  {
    id: 'failures',
    title: 'Unresolved Failures',
    items: [
      { id: 'f1', label: 'Orchestrator retry exhausted', meta: 'open 18m' }
    ]
  }
];
