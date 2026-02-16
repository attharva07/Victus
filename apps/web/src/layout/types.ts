export type LaneId = 'LEFT_RAIL' | 'FOCUS' | 'CONTEXT' | 'BOTTOM_STRIP';

export type WidgetSize = 'XS' | 'S' | 'M' | 'L' | 'XL';

export type WidgetId =
  | 'dialogue'
  | 'systemOverview'
  | 'timeline'
  | 'healthPulse'
  | 'reminders'
  | 'alerts'
  | 'approvals'
  | 'workflows'
  | 'failures';

export type WidgetDefinition = {
  id: WidgetId;
  lane: Extract<LaneId, 'FOCUS' | 'CONTEXT'>;
  allowedSizes: WidgetSize[];
  defaultSize: WidgetSize;
  minSize: WidgetSize;
  maxSize: WidgetSize;
  urgency: number;
  confidence: number;
  pinned?: boolean;
  failureBoost?: number;
  approvalBoost?: number;
};

export type LayoutEngineConfig = {
  urgencyWeight: number;
  confidenceWeight: number;
  pinnedBoost: number;
  highUrgencyThreshold: number;
  recomputeIntervalMs: number;
  debug: boolean;
};

export type WidgetRuntimeSignals = Partial<Record<WidgetId, {
  urgency?: number;
  confidence?: number;
  pinned?: boolean;
  failureBoost?: number;
  approvalBoost?: number;
}>>;

export type ScoredWidget = WidgetDefinition & {
  score: number;
  scoreBreakdown: {
    urgency: number;
    confidence: number;
    pinnedBoost: number;
    failureBoost: number;
    approvalBoost: number;
  };
  size: WidgetSize;
};

export type FocusPlacement = {
  id: WidgetId;
  row: number;
  colStart: number;
  span: number;
  size: WidgetSize;
};

export type LayoutPlan = {
  computedAt: number;
  focusPlacements: FocusPlacement[];
  contextOrder: WidgetId[];
  scores: Record<WidgetId, ScoredWidget['scoreBreakdown'] & { total: number }>;
};


// Back-compat types for legacy components still present in tree.
export type VictusCardId = WidgetId | 'worldTldr';
export type CardState = 'focus' | 'peek' | 'chip';
export type LayoutPreset = 'CALM' | 'ACTIVE' | 'STABILIZE' | 'DIALOGUE';
