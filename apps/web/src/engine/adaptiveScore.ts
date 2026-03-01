export type AdaptiveKind = 'reminder' | 'approval' | 'alert' | 'failure' | 'workflow' | 'dialogue' | 'timeline';
export type AdaptiveSeverity = 'info' | 'warning' | 'critical';

export type AdaptiveItem = {
  id: string;
  kind: AdaptiveKind;
  title: string;
  detail: string;
  status: string;
  urgency: number;
  confidenceImpact: number;
  severity?: AdaptiveSeverity;
  updatedAt: number;
  actions: Array<'approve' | 'deny' | 'done' | 'resume' | 'open'>;
};

export const SCORE_WEIGHTS = {
  urgency: 0.6,
  confidenceSignal: 0.3,
  recencyBoost: 0.1,
  severityBoost: {
    critical: 18,
    warning: 8,
    info: 0
  }
} as const;

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

export function confidenceSignalForItem(item: AdaptiveItem): number {
  if (item.kind === 'failure') return clamp(55 - item.confidenceImpact, 0, 100);
  if (item.kind === 'alert') return clamp(50 - item.confidenceImpact * 0.8, 0, 100);
  if (item.kind === 'workflow') return clamp(50 + item.confidenceImpact * 0.5, 0, 100);
  if (item.kind === 'approval') return clamp(52 - item.confidenceImpact * 0.4, 0, 100);
  if (item.kind === 'dialogue' || item.kind === 'timeline') return clamp(45 + item.confidenceImpact * 0.25, 0, 100);
  return clamp(50 + item.confidenceImpact * 0.6, 0, 100);
}

export function recencyBoost(item: AdaptiveItem, now = Date.now()): number {
  const minutes = Math.max(0, (now - item.updatedAt) / 60_000);
  if (minutes <= 5) return 100;
  if (minutes <= 30) return 80;
  if (minutes <= 120) return 55;
  if (minutes <= 360) return 30;
  return 10;
}

export function compositeScore(item: AdaptiveItem, now = Date.now()): number {
  const confidenceSignal = confidenceSignalForItem(item);
  const recency = recencyBoost(item, now);
  const base =
    SCORE_WEIGHTS.urgency * clamp(item.urgency, 0, 100) +
    SCORE_WEIGHTS.confidenceSignal * confidenceSignal +
    SCORE_WEIGHTS.recencyBoost * recency;

  const severityBoost = item.kind === 'failure' || (item.kind === 'alert' && item.severity === 'critical')
    ? SCORE_WEIGHTS.severityBoost[item.severity ?? 'info']
    : 0;

  return Number((base + severityBoost).toFixed(2));
}
