export type VictusLane = 'FOCUS' | 'CONTEXT';
export type CardSize = 'S' | 'M' | 'L';
export type CardRole = 'primary' | 'secondary' | 'tertiary';

export type CardId =
  | 'dialogue'
  | 'timeline'
  | 'healthPulse'
  | 'systemOverview'
  | 'worldTldr'
  | 'workflowsBoard'
  | 'remindersPanel'
  | 'approvalsPanel'
  | 'failures'
  | 'approvals'
  | 'alerts'
  | 'reminders'
  | 'workflows';

export type CardPrioritySignals = {
  urgency: number;
  confidenceWeight: number;
  freshnessMs?: number;
  volume?: number;
};

export type VictusCard = {
  id: CardId;
  lane: VictusLane;
  size: CardSize;
  pinned: boolean;
  expanded: boolean;
  role: CardRole;
  priority: CardPrioritySignals;
};

export type Severity = 'info' | 'warning' | 'critical';

export type FailureItem = { id: string; title: string; severity: Severity; ageMinutes: number };
export type ApprovalItem = { id: string; title: string; detail: string; requestedBy: string };
export type AlertItem = { id: string; title: string; detail: string; acknowledged?: boolean };
export type ReminderItem = { id: string; title: string; due: string; urgency: 'low' | 'medium' | 'high'; done?: boolean };
export type WorkflowItem = { id: string; title: string; progress: number; stepLabel: string; resumable?: boolean };

export type ContextGroups = {
  approvals: ApprovalItem[];
  alerts: AlertItem[];
  reminders: ReminderItem[];
  workflows: WorkflowItem[];
  failures: FailureItem[];
};

export type TimelineBucket = 'Today' | 'Upcoming' | 'Completed';
export type TimelineEvent = {
  id: string;
  bucket: TimelineBucket;
  label: string;
  detail: string;
  createdAt: number;
};

export type TimelineState = {
  today: TimelineEvent[];
  upcoming: TimelineEvent[];
  completed: TimelineEvent[];
};

export type DialogueMessage = { id: string; role: 'user' | 'system'; text: string; createdAt: number };

export type BottomStripStatus = {
  mode: string;
  planner: string;
  executor: string;
  domain: string;
  confidence: number;
};

export type VictusUIState = {
  cards: Record<CardId, VictusCard>;
  contextGroups: ContextGroups;
  timeline: TimelineState;
  dialogue: { messages: DialogueMessage[] };
  worldTldr: string[];
  bottomStrip: BottomStripStatus;
  lastUserInputAt: number;
};

export type ApprovalDecision = 'approved' | 'denied';
