import type { LayoutSignals, Severity } from './signals';
import type { CardPlacement, CardSize, LayoutPlan, Zone } from './types';

type CardId =
  | 'systemOverview'
  | 'dialogue'
  | 'timeline'
  | 'worldTldr'
  | 'reminders'
  | 'alerts'
  | 'approvals'
  | 'workflows'
  | 'failures';

type CardScore = {
  id: CardId;
  zone: Zone;
  urgencyScore: number;
  confidenceFactor: number;
  finalScore: number;
};

type PolicyResult = {
  preset: LayoutPlan['preset'];
  activeCardId?: string;
  forceDominantCenter?: CardId;
  forceDominantRight?: CardId;
  minimumSizeByCard: Partial<Record<CardId, CardSize>>;
};

const severityBump: Record<Severity, number> = {
  none: 0,
  low: 5,
  medium: 12,
  high: 20,
  critical: 32
};

const tieBreakOrder: CardId[] = [
  'systemOverview',
  'dialogue',
  'failures',
  'approvals',
  'alerts',
  'reminders',
  'workflows',
  'timeline',
  'worldTldr'
];

const cardZones: Record<CardId, Zone> = {
  systemOverview: 'center',
  dialogue: 'center',
  timeline: 'center',
  worldTldr: 'center',
  reminders: 'right',
  alerts: 'right',
  approvals: 'right',
  workflows: 'right',
  failures: 'right'
};

const dominantHoldSeconds = 45;
const dominantSwitchDelta = 8;

function scoreForCard(signals: LayoutSignals, id: CardId): number {
  switch (id) {
    case 'failures':
      return 70 + severityBump[signals.failuresSeverity] + Math.min(signals.failuresCount * 5, 20);
    case 'approvals':
      return 60 + Math.min(signals.approvalsPending * 8, 30);
    case 'alerts':
      return 55 + severityBump[signals.alertsSeverity] + Math.min(signals.alertsCount * 4, 16);
    case 'reminders':
      return 45 + Math.min(signals.remindersDueToday * 7, 28) + Math.min(signals.remindersCount * 2, 10);
    case 'dialogue':
      return signals.dialogueOpen ? 80 : 30;
    case 'timeline':
      return 35 + (signals.remindersDueToday > 0 ? 8 : 0);
    case 'worldTldr':
      return 20;
    case 'systemOverview':
      return 50;
    case 'workflows':
      return 40 + Math.min(signals.workflowsActive * 4, 16);
  }
}

function sizeFromScore(score: number): CardSize {
  if (score >= 90) return 'XL';
  if (score >= 70) return 'L';
  if (score >= 50) return 'M';
  if (score >= 30) return 'S';
  return 'XS';
}

function maxSize(a: CardSize, b: CardSize): CardSize {
  const rank: CardSize[] = ['XS', 'S', 'M', 'L', 'XL'];
  return rank[Math.max(rank.indexOf(a), rank.indexOf(b))];
}

function applyPolicies(signals: LayoutSignals): PolicyResult {
  const result: PolicyResult = {
    preset: 'P1',
    minimumSizeByCard: { systemOverview: 'M' }
  };

  if (signals.dialogueOpen) {
    if (signals.confidenceScore < 25) {
      result.preset = 'P2';
      result.forceDominantRight = 'failures';
      result.minimumSizeByCard.dialogue = 'M';
    } else {
      result.preset = 'P3';
      result.activeCardId = 'dialogue';
      result.forceDominantCenter = 'dialogue';
      result.minimumSizeByCard.dialogue = 'XL';
    }
  } else if (signals.confidence === 'unstable' || signals.confidenceScore < 40) {
    result.preset = 'P2';
    result.forceDominantRight = 'failures';
  }

  return result;
}

function scoreCards(signals: LayoutSignals): CardScore[] {
  const confidenceFactor = 0.6 + 0.4 * (signals.confidenceScore / 100);

  return (Object.keys(cardZones) as CardId[])
    .map((id) => {
      const urgencyScore = scoreForCard(signals, id);
      return {
        id,
        zone: cardZones[id],
        urgencyScore,
        confidenceFactor,
        finalScore: urgencyScore * confidenceFactor
      };
    })
    .sort((a, b) => {
      if (b.finalScore !== a.finalScore) return b.finalScore - a.finalScore;
      return tieBreakOrder.indexOf(a.id) - tieBreakOrder.indexOf(b.id);
    });
}

function getPlacementScore(placements: CardPlacement[], id: string): number {
  const sizeScore: Record<CardSize, number> = { XS: 20, S: 40, M: 60, L: 80, XL: 100 };
  const match = placements.find((placement) => placement.id === id);
  if (!match) return 0;
  return sizeScore[match.size] - (match.collapsed ? 10 : 0);
}

function dominantCardForZone(placements: CardPlacement[], zone: Zone): string | undefined {
  return placements
    .filter((placement) => placement.zone === zone)
    .sort((a, b) => getPlacementScore(placements, b.id) - getPlacementScore(placements, a.id) || a.priority - b.priority)[0]?.id;
}

function chooseSizesAndStacking(
  scored: CardScore[],
  policy: PolicyResult,
  signals: LayoutSignals,
  prev?: LayoutPlan
): { placements: CardPlacement[]; activeCardId?: string } {
  const center = scored.filter((card) => card.zone === 'center');
  const right = scored.filter((card) => card.zone === 'right');

  const topCenter = policy.forceDominantCenter ? center.find((card) => card.id === policy.forceDominantCenter) ?? center[0] : center[0];

  const centerDominantTarget = topCenter?.id;
  const prevCenterDominant = prev ? dominantCardForZone(prev.placements, 'center') : undefined;
  const signalAge = prev ? Math.max(0, (signals.updatedAt - prev.generatedAt) / 1000) : dominantHoldSeconds + 1;

  let dominantCenter = centerDominantTarget;
  if (
    prev &&
    prevCenterDominant &&
    centerDominantTarget &&
    prevCenterDominant !== centerDominantTarget &&
    signalAge < dominantHoldSeconds &&
    signals.failuresSeverity !== 'critical'
  ) {
    const candidateScore = center.find((card) => card.id === centerDominantTarget)?.finalScore ?? 0;
    const prevScore = center.find((card) => card.id === prevCenterDominant)?.finalScore ?? 0;
    if (candidateScore - prevScore < dominantSwitchDelta) {
      dominantCenter = prevCenterDominant as CardId;
    }
  }

  const placements: CardPlacement[] = [];

  const sortedCenter = [...center].sort((a, b) => {
    if (a.id === dominantCenter) return -1;
    if (b.id === dominantCenter) return 1;
    if (b.finalScore !== a.finalScore) return b.finalScore - a.finalScore;
    return tieBreakOrder.indexOf(a.id) - tieBreakOrder.indexOf(b.id);
  });

  sortedCenter.forEach((card, index) => {
    let size = sizeFromScore(card.finalScore);
    if (index === 0) {
      size = card.finalScore >= 80 ? 'XL' : 'L';
    } else if (index <= 2 && size === 'XS') {
      size = 'S';
    }

    const minimumSize = policy.minimumSizeByCard[card.id];
    if (minimumSize) size = maxSize(size, minimumSize);

    placements.push({
      id: card.id,
      zone: 'center',
      size,
      collapsed: size === 'XS',
      priority: index
    });
  });

  const sortedRight = [...right].sort((a, b) => {
    if (policy.forceDominantRight === a.id) return -1;
    if (policy.forceDominantRight === b.id) return 1;
    if (b.finalScore !== a.finalScore) return b.finalScore - a.finalScore;
    return tieBreakOrder.indexOf(a.id) - tieBreakOrder.indexOf(b.id);
  });

  sortedRight.forEach((card, index) => {
    let size = sizeFromScore(card.finalScore);
    if (index === 0 && size === 'M') size = 'L';
    if (policy.forceDominantRight === card.id) size = maxSize(size, 'L');

    placements.push({
      id: card.id,
      zone: 'right',
      size,
      collapsed: size === 'XS',
      priority: index
    });
  });

  const nextActiveCardId = policy.activeCardId ?? (policy.preset === 'P2' ? dominantCenter : undefined);
  return { placements, activeCardId: nextActiveCardId };
}

export function generateLayoutPlan(signals: LayoutSignals, prev?: LayoutPlan): LayoutPlan {
  const policy = applyPolicies(signals);
  const scored = scoreCards(signals);
  const { placements, activeCardId } = chooseSizesAndStacking(scored, policy, signals, prev);

  return {
    preset: policy.preset,
    placements,
    activeCardId,
    generatedAt: signals.updatedAt,
    ttlSeconds: 300
  };
}
