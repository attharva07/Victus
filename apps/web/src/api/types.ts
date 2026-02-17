export type EntityKind = 'reminder' | 'approval' | 'alert' | 'failure' | 'workflow' | 'dialogue' | 'timeline';

export type UIEntity = {
  id: string;
  title: string;
  detail: string;
  status: string;
  urgency: number;
  updated_at: number;
  severity?: 'info' | 'warning' | 'critical';
};

export type WorkflowEntity = UIEntity & {
  progress: number;
  step: number;
  total_steps: number;
};

export type FocusLaneCard = {
  id: string;
  kind: EntityKind;
};

export type DialogueMessage = {
  id: string;
  role: 'user' | 'system';
  text: string;
  created_at: number;
};

export type TimelineEvent = {
  id: string;
  label: string;
  detail: string;
  created_at: number;
};

export type UIStateResponse = {
  reminders: UIEntity[];
  approvals: UIEntity[];
  alerts: UIEntity[];
  failures: UIEntity[];
  workflows: WorkflowEntity[];
  focus_lane_cards: FocusLaneCard[];
  dialogue_messages: DialogueMessage[];
  timeline_events: TimelineEvent[];
};
