import type { MockUiState } from '../state/mockState';

export type LaneId = 'LEFT_RAIL' | 'FOCUS' | 'CONTEXT' | 'BOTTOM_STRIP';
export type WidgetSize = 'S' | 'M' | 'L';
export type WidgetRole = 'primary' | 'secondary' | 'tertiary';

export type WidgetId =
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

export type WidgetDefinition = {
  id: WidgetId;
  lane: Extract<LaneId, 'FOCUS' | 'CONTEXT'>;
  role: WidgetRole;
  sizePreset: WidgetSize;
  heightHint: number;
  pinable: boolean;
  expandable: boolean;
  visibleWhen: (state: MockUiState, pinned: boolean) => boolean;
  score: (state: MockUiState) => number;
};

export type FocusPlacement = {
  id: WidgetId;
  score: number;
  role: WidgetRole;
  sizePreset: WidgetSize;
  heightHint: number;
  column: 'left' | 'right';
};

export type LayoutPlan = {
  computedAt: number;
  focusPlacements: FocusPlacement[];
  contextOrder: WidgetId[];
  dominantCardId?: VictusCardId;
  supportingCardIds?: VictusCardId[];
  compactCardIds?: VictusCardId[];
  cardStates?: Partial<Record<VictusCardId, CardState>>;
};

export type LayoutEngineConfig = {
  urgencyWeight: number;
  confidenceMultiplierBase: number;
};

export type VictusCardId = WidgetId | 'worldTldr';
export type CardState = 'focus' | 'peek' | 'chip';
export type LayoutPreset = 'CALM' | 'ACTIVE' | 'STABILIZE' | 'DIALOGUE';
