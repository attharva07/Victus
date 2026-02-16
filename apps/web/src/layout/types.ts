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

export type LayoutPlan = {
  dominantCardId: VictusCardId;
  supportingCardIds: VictusCardId[];
  compactCardIds: VictusCardId[];
  rightContextCardIds: VictusCardId[];
  preset: LayoutPreset;
  generatedAt: number;
  ttlSeconds: number;
};
