import type { LayoutSignals, Severity } from './signals';
import type { CardPlacement, CardSize, LayoutPlan } from './types';

type AllowedSet = {
  center: string[];
  right: string[];
  dialogueOnly: boolean;
};

type ScoredCard = {
  id: string;
  zone: 'center' | 'right';
  score: number;
  priority: number;
};

const severityRank: Record<Severity, number> = {
  none: 0,
  low: 1,
  medium: 2,
  high: 3,
  critical: 4
};

const baseWeights: Record<string, number> = {
  failures: 80,
  approvals: 70,
  alerts: 65,
  reminders: 50,
  workflows: 45,
  timeline: 40,
  world_tldr: 20,
  system_overview: 55,
  dialogue: 100
};

const basePriority: Record<string, number> = {
  system_overview: 1,
  timeline: 2,
  world_tldr: 3,
  dialogue: 0,
  reminders: 10,
  alerts: 11,
  approvals: 12,
  workflows: 13,
  failures: 14
};

export function applyPolicies(signals: LayoutSignals): AllowedSet {
  if (signals.dialogueOpen) {
    return {
      center: ['dialogue'],
      right: [],
      dialogueOnly: true
    };
  }

  return {
    center: ['system_overview', 'timeline', 'world_tldr'],
    right: ['reminders', 'alerts', 'approvals', 'workflows', 'failures'],
    dialogueOnly: false
  };
}

export function scoreCards(signals: LayoutSignals, allowed: AllowedSet): ScoredCard[] {
  const scopedCards = [
    ...allowed.center.map((id) => ({ id, zone: 'center' as const })),
    ...allowed.right.map((id) => ({ id, zone: 'right' as const }))
  ];

  return scopedCards
    .map(({ id, zone }) => {
      let score = baseWeights[id] ?? 10;

      if (id === 'failures' && signals.failuresCount > 0 && severityRank[signals.failuresSeverity] >= severityRank.high) {
        score += 30;
      }
      if (id === 'approvals' && signals.approvalsPending > 0) {
        score += 25;
      }
      if (id === 'alerts' && severityRank[signals.alertsSeverity] >= severityRank.medium) {
        score += 20;
      }
      if (id === 'reminders' && signals.remindersCount > 0) {
        score += 15;
      }
      if (signals.confidence === 'unstable' && (id === 'alerts' || id === 'failures')) {
        score += 15;
      }
      if (signals.confidence === 'drifting' && id === 'alerts') {
        score += 8;
      }
      if (id === 'workflows' && signals.workflowsActive > 0) {
        score += 12;
      }
      if (id === 'timeline' && (signals.remindersCount + signals.workflowsActive) > 2) {
        score += 10;
      }

      return {
        id,
        zone,
        score,
        priority: basePriority[id] ?? 999
      };
    })
    .sort((a, b) => b.score - a.score || a.priority - b.priority || a.id.localeCompare(b.id));
}

export function choosePreset(signals: LayoutSignals): LayoutPlan['preset'] {
  if (signals.dialogueOpen) return 'P3';

  const density =
    signals.remindersCount +
    signals.alertsCount +
    signals.failuresCount +
    signals.approvalsPending +
    signals.workflowsActive;

  const mixedSignals = [signals.alertsCount > 0, signals.failuresCount > 0, signals.approvalsPending > 0, signals.workflowsActive > 0].filter(Boolean).length;

  if (density >= 4 && mixedSignals >= 2) {
    return 'P2';
  }

  return 'P1';
}

function toSize(score: number): CardSize {
  if (score >= 120) return 'XL';
  if (score >= 90) return 'L';
  if (score >= 60) return 'M';
  if (score >= 30) return 'S';
  return 'XS';
}

export function chooseSizesAndOrder(scored: ScoredCard[]): CardPlacement[] {
  return scored
    .map((card) => {
      const size = toSize(card.score);
      const colSpan = card.zone === 'right' ? 1 : size === 'XL' ? 2 : 1;

      return {
        id: card.id,
        zone: card.zone,
        size,
        colSpan,
        priority: card.priority
      } as CardPlacement;
    })
    .sort((a, b) => a.zone.localeCompare(b.zone) || a.priority - b.priority || a.id.localeCompare(b.id));
}

export function generateLayoutPlan(signals: LayoutSignals): LayoutPlan {
  const allowed = applyPolicies(signals);
  const preset = choosePreset(signals);

  if (allowed.dialogueOnly) {
    return {
      preset,
      activeCardId: 'dialogue',
      generatedAt: signals.updatedAt,
      ttlSeconds: 120,
      placements: [
        {
          id: 'dialogue',
          zone: 'center',
          size: 'XL',
          colSpan: 2,
          priority: 0
        }
      ]
    };
  }

  const placements = chooseSizesAndOrder(scoreCards(signals, allowed));

  return {
    preset,
    placements,
    generatedAt: signals.updatedAt,
    ttlSeconds: 120
  };
}
