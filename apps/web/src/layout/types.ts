export type CardSize = 'XS' | 'S' | 'M' | 'L' | 'XL';
export type Zone = 'center' | 'right';
export type Preset = 'P1' | 'P2' | 'P3' | 'P4' | 'P5';

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
  activeCardId?: string;
  generatedAt: number;
  ttlSeconds: number;
};
