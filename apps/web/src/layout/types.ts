export type CardSize = 'XS' | 'S' | 'M' | 'L' | 'XL';
export type Zone = 'center' | 'right';
export type Preset = 'P1' | 'P2' | 'P3' | 'P4' | 'P5';

export type ColumnSplit = 'balanced' | 'centerFocus' | 'rightFocus';

export type CardPlacement = {
  id: string;
  zone: Zone;
  size: CardSize;
  collapsed?: boolean;
  priority: number;
};

export type LayoutPlan = {
  preset: Preset;
  placements: CardPlacement[];
  splitColumns: ColumnSplit;
  activeCardId?: string;
  generatedAt: number;
  ttlSeconds: number;
};
