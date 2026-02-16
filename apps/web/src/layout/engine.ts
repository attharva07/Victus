import type { LayoutSignals, Severity } from './signals';
import type { CardState, LayoutPlan, LayoutPreset, VictusCardId } from './types';

type ScoredCard = {
  id: VictusCardId;
  urgencyScore: number;
  finalScore: number;
};

const centerLaneCards: VictusCardId[] = ['systemOverview', 'dialogue', 'failures', 'timeline', 'worldTldr'];
const rightContextCards: VictusCardId[] = ['failures', 'approvals', 'alerts', 'reminders', 'workflows'];
const scoreTieBreak: VictusCardId[] = [
  'failures',
  'dialogue',
  'approvals',
  'alerts',
  'reminders',
  'workflows',
  'systemOverview',
  'timeline',
  'worldTldr'
];

const severityWeight: Record<Severity, number> = {
  none: 0,
  low: 8,
  medium: 16,
  high: 24,
  critical: 35
};

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

function urgencyForCard(id: VictusCardId, signals: LayoutSignals): number {
  switch (id) {
    case 'systemOverview':
      return clamp(40 + signals.workflowsActive * 4 + signals.approvalsPending * 3, 25, 90);
    case 'dialogue':
      return clamp((signals.dialogueOpen ? 65 : 25) + (signals.userTyping ? 20 : 0), 10, 100);
    case 'failures':
      return clamp(45 + severityWeight[signals.failuresSeverity] + signals.failuresCount * 8, 10, 100);
    case 'reminders':
      return clamp(30 + signals.remindersCount * 6 + signals.remindersDueToday * 10, 0, 100);
    case 'approvals':
      return clamp(35 + signals.approvalsPending * 12, 0, 100);
    case 'alerts':
      return clamp(30 + severityWeight[signals.alertsSeverity] + signals.alertsCount * 7, 0, 100);
    case 'workflows':
      return clamp(26 + signals.workflowsActive * 9, 0, 100);
    case 'timeline':
      return clamp(28 + signals.remindersDueToday * 5 + (signals.dialogueOpen ? 8 : 0), 0, 90);
    case 'worldTldr':
      return 20;
  }
}

function sortScoredCards(cards: ScoredCard[]): ScoredCard[] {
  return [...cards].sort((a, b) => {
    if (a.finalScore !== b.finalScore) return b.finalScore - a.finalScore;
    return scoreTieBreak.indexOf(a.id) - scoreTieBreak.indexOf(b.id);
  });
}

function getPreset(signals: LayoutSignals, dominantCardId: VictusCardId): LayoutPreset {
  if (dominantCardId === 'dialogue') return 'DIALOGUE';
  if (dominantCardId === 'failures') return 'STABILIZE';

  const load = signals.approvalsPending + signals.remindersDueToday + signals.workflowsActive + signals.alertsCount;
  return load >= 8 ? 'ACTIVE' : 'CALM';
}

export function generateLayoutPlan(signals: LayoutSignals): LayoutPlan {
  const confidenceFactor = 0.6 + 0.4 * (signals.confidenceScore / 100);

  const scored = sortScoredCards(
    scoreTieBreak.map((id) => {
      const urgencyScore = urgencyForCard(id, signals);
      return {
        id,
        urgencyScore,
        finalScore: urgencyScore * confidenceFactor
      };
    })
  );

  let dominantCardId: VictusCardId = scored[0]?.id ?? 'systemOverview';

  if (signals.failuresSeverity === 'critical' || signals.confidenceScore < 25) {
    dominantCardId = 'failures';
  } else if (signals.dialogueOpen && signals.confidenceScore >= 25) {
    dominantCardId = 'dialogue';
  }

  const rankedCenter = sortScoredCards(scored.filter((card) => centerLaneCards.includes(card.id)));
  const centerWithoutDominant = rankedCenter.filter((card) => card.id !== dominantCardId);

  const supportingCardIds: VictusCardId[] = [];
  const compactCardIds: VictusCardId[] = [];

  if (centerWithoutDominant.length > 0) {
    for (const card of centerWithoutDominant) {
      if (supportingCardIds.length < 4 && card.finalScore >= 30) {
        supportingCardIds.push(card.id);
      } else {
        compactCardIds.push(card.id);
      }
    }
  }

  if (!supportingCardIds.includes('systemOverview') && dominantCardId !== 'systemOverview') {
    supportingCardIds.unshift('systemOverview');
    const dedup = Array.from(new Set(supportingCardIds));
    supportingCardIds.splice(0, supportingCardIds.length, ...dedup.slice(0, 4));
    const compactSet = new Set(compactCardIds);
    compactSet.delete('systemOverview');
    compactCardIds.splice(0, compactCardIds.length, ...compactSet);
  }

  const rightContextCardIds = sortScoredCards(scored.filter((card) => rightContextCards.includes(card.id))).map((card) => card.id);

  if (dominantCardId === 'failures') {
    const remaining = rightContextCardIds.filter((id) => id !== 'failures');
    rightContextCardIds.splice(0, rightContextCardIds.length, 'failures', ...remaining);
  }

  const cardStates: Partial<Record<VictusCardId, CardState>> = {
    [dominantCardId]: 'focus'
  };

  supportingCardIds.forEach((id) => {
    cardStates[id] = 'peek';
  });

  compactCardIds.forEach((id) => {
    cardStates[id] = 'chip';
  });

  return {
    dominantCardId,
    supportingCardIds,
    compactCardIds,
    cardStates,
    rightContextCardIds,
    preset: getPreset(signals, dominantCardId),
    generatedAt: Date.now(),
    ttlSeconds: 180
  };
}
