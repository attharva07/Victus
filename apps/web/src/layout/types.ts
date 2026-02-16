export type CardSize = 'XS' | 'S' | 'M' | 'L' | 'XL';

export type Zone = 'center' | 'right';

export type ColSpan = 1 | 2;

export type CardPlacement = {
  id: string;
  zone: Zone;
  size: CardSize;
  colSpan: ColSpan;
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
