import { contextWidgetIds, focusWidgetIds, widgetRegistry } from './registry';
import type {
  FocusPlacement,
  LayoutEngineConfig,
  LayoutPlan,
  ScoredWidget,
  WidgetId,
  WidgetRole,
  WidgetRuntimeSignals,
  WidgetSize
} from './types';

const heightHintBySize: Record<WidgetSize, number> = {
  XS: 2,
  S: 3,
  M: 5,
  L: 7,
  XL: 9
};

const roleWeight: Record<WidgetRole, number> = {
  primary: 0,
  secondary: 1,
  tertiary: 2
};

const tieBreakOrder: WidgetId[] = [
  'dialogue',
  'systemOverview',
  'timeline',
  'healthPulse',
  'approvals',
  'failures',
  'alerts',
  'reminders',
  'workflows'
];

export const defaultEngineConfig: LayoutEngineConfig = {
  urgencyWeight: 0.65,
  confidenceWeight: 0.35,
  pinnedBoost: 20,
  highUrgencyThreshold: 82,
  recomputeIntervalMs: 5 * 60 * 1000,
  debug: false
};

function clamp(value: number): number {
  return Math.max(0, Math.min(100, value));
}

function chooseSize(score: number, allowed: WidgetSize[]): WidgetSize {
  if (score >= 88 && allowed.includes('XL')) return 'XL';
  if (score >= 76 && allowed.includes('L')) return 'L';
  if (score >= 58 && allowed.includes('M')) return 'M';
  if (score >= 32 && allowed.includes('S')) return 'S';
  return allowed.includes('XS') ? 'XS' : allowed[0];
}

function scoreWidgets(signals: WidgetRuntimeSignals, config: LayoutEngineConfig): ScoredWidget[] {
  return Object.values(widgetRegistry).map((widget) => {
    const runtime = signals[widget.id] ?? {};
    const urgency = clamp(runtime.urgency ?? widget.urgency);
    const confidence = clamp(runtime.confidence ?? widget.confidence);
    const pinned = runtime.pinned ?? widget.pinned ?? false;
    const failureBoost = runtime.failureBoost ?? widget.failureBoost ?? 0;
    const approvalBoost = runtime.approvalBoost ?? widget.approvalBoost ?? 0;
    const score = urgency * config.urgencyWeight + confidence * config.confidenceWeight + (pinned ? config.pinnedBoost : 0) + failureBoost + approvalBoost;

    return {
      ...widget,
      role: runtime.role ?? 'secondary',
      size: chooseSize(score, widget.allowedSizes),
      score,
      scoreBreakdown: {
        urgency: urgency * config.urgencyWeight,
        confidence: confidence * config.confidenceWeight,
        pinnedBoost: pinned ? config.pinnedBoost : 0,
        failureBoost,
        approvalBoost
      }
    };
  });
}

function deterministicSort(items: ScoredWidget[]): ScoredWidget[] {
  return [...items].sort((a, b) => {
    if (roleWeight[a.role] !== roleWeight[b.role]) return roleWeight[a.role] - roleWeight[b.role];
    if (a.score !== b.score) return b.score - a.score;
    if (a.id !== b.id) return a.id.localeCompare(b.id);
    return tieBreakOrder.indexOf(a.id) - tieBreakOrder.indexOf(b.id);
  });
}

function packFocus(sortedFocus: ScoredWidget[]): FocusPlacement[] {
  const placements: FocusPlacement[] = [];
  const columns = {
    left: 0,
    right: 0
  };

  sortedFocus.forEach((widget) => {
    const heightHint = heightHintBySize[widget.size];
    const column = columns.left <= columns.right ? 'left' : 'right';
    columns[column] += heightHint;

    placements.push({
      id: widget.id,
      score: widget.score,
      role: widget.role,
      sizePreset: widget.size,
      heightHint,
      column
    });
  });

  return placements;
}

export function buildLayoutPlan(signals: WidgetRuntimeSignals, config: LayoutEngineConfig = defaultEngineConfig): LayoutPlan {
  const scored = deterministicSort(scoreWidgets(signals, config));
  const focus = scored.filter((entry) => focusWidgetIds.includes(entry.id));
  const context = scored.filter((entry) => contextWidgetIds.includes(entry.id));

  if (config.debug) {
    // eslint-disable-next-line no-console
    console.debug('[layout-engine:scores]', scored.map((w) => ({ id: w.id, role: w.role, score: Number(w.score.toFixed(2)), ...w.scoreBreakdown })));
  }

  return {
    computedAt: Date.now(),
    focusPlacements: packFocus(focus),
    contextOrder: context.map((entry) => entry.id),
    scores: scored.reduce((acc, widget) => {
      acc[widget.id] = { ...widget.scoreBreakdown, total: widget.score };
      return acc;
    }, {} as LayoutPlan['scores'])
  };
}

export function needsUrgentRecompute(signals: WidgetRuntimeSignals, config: LayoutEngineConfig = defaultEngineConfig): boolean {
  const approvalsUrgency = signals.approvals?.urgency ?? 0;
  const failureUrgency = signals.failures?.urgency ?? 0;
  const maxUrgency = Math.max(...Object.values(signals).map((signal) => signal?.urgency ?? 0), 0);

  return approvalsUrgency >= config.highUrgencyThreshold || failureUrgency >= config.highUrgencyThreshold || maxUrgency >= config.highUrgencyThreshold;
}
