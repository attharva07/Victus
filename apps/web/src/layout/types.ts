export type CardSize = 'XS' | 'S' | 'M' | 'L' | 'XL';

export type Zone = 'center' | 'right';

export type CardPlacement = {
  id: string;
  zone: Zone;
  size: CardSize;
  collapsed?: boolean;
  priority: number;
};

export type LayoutPlan = {
  preset: 'P1' | 'P2' | 'P3';
  placements: CardPlacement[];
  activeCardId?: string;
  generatedAt: number;
  ttlSeconds: number;
};
