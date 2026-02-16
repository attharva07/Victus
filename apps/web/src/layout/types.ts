export type VictusCardId =
  | 'systemOverview'
  | 'dialogue'
  | 'timeline'
  | 'worldTldr'
  | 'failures'
  | 'reminders'
  | 'approvals'
  | 'alerts'
  | 'workflows';

export type LayoutPreset = 'CALM' | 'ACTIVE' | 'STABILIZE' | 'DIALOGUE';
export type CardState = 'focus' | 'peek' | 'chip';

export type LayoutPlan = {
  dominantCardId: VictusCardId;
  supportingCardIds: VictusCardId[];
  compactCardIds: VictusCardId[];
  cardStates: Partial<Record<VictusCardId, CardState>>;
  rightContextCardIds: VictusCardId[];
  preset: LayoutPreset;
  generatedAt: number;
  ttlSeconds: number;
};
