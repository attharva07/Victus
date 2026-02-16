import type { CardId, CardSize, CardRole, VictusUIState } from '../types/victus-ui';

export type LaneId = 'LEFT_RAIL' | 'FOCUS' | 'CONTEXT' | 'BOTTOM_STRIP';
export type WidgetSize = CardSize;
export type WidgetRole = CardRole;
export type WidgetId = CardId;

export type WidgetDefinition = {
  id: WidgetId;
  lane: Extract<LaneId, 'FOCUS' | 'CONTEXT'>;
  role: WidgetRole;
  sizePreset: WidgetSize;
  heightHint: number;
  pinable: boolean;
  expandable: boolean;
  visibleWhen: (state: VictusUIState, pinned: boolean) => boolean;
  score: (state: VictusUIState) => number;
};

export type FocusPlacement = {
  id: WidgetId;
  score: number;
  role: WidgetRole;
  sizePreset: WidgetSize;
  heightHint: number;
  column: 'left' | 'right';
};

export type PinnedAnchor = 'top' | 'normal';

export type FocusPinState = { pinned: boolean; col: 0 | 1; order: number; anchor: PinnedAnchor };
export type FocusPinMap = Partial<Record<WidgetId, FocusPinState>>;

export type LayoutPlan = {
  computedAt: number;
  focusPlacements: FocusPlacement[];
  contextOrder: WidgetId[];
  dominantCardId?: VictusCardId;
  supportingCardIds?: VictusCardId[];
  compactCardIds?: VictusCardId[];
  cardStates?: Partial<Record<VictusCardId, CardState>>;
};

export type LayoutEngineConfig = { urgencyWeight: number; confidenceMultiplierBase: number };

export type VictusCardId = WidgetId | 'worldTldr';
export type CardState = 'focus' | 'peek' | 'chip';
export type LayoutPreset = 'CALM' | 'ACTIVE' | 'STABILIZE' | 'DIALOGUE';
