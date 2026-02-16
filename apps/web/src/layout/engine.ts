import type { LayoutSignals, Severity } from './signals';
import type { CardPlacement, ColumnSplit, LayoutPlan, Preset } from './types';

const severityWeight: Record<Severity, number> = {
  none: 0,
  low: 1,
  medium: 2,
  high: 3,
  critical: 4
};

const presetOrder: Preset[] = ['P5', 'P4', 'P3', 'P2', 'P1'];

const centerCardIds = ['system_overview', 'dialogue', 'timeline', 'world_tldr'] as const;
const rightCardIds = ['failures', 'alerts', 'approvals', 'workflows', 'reminders'] as const;

type ScoreMap = Record<Preset, number>;

const withPriority = (ids: readonly string[], zone: CardPlacement['zone'], sizes: Record<string, CardPlacement['size']>): CardPlacement[] =>
  ids.map((id, index) => ({
    id,
    zone,
    size: sizes[id] ?? 'S',
    priority: index + 1
  }));

const pickPreset = (scores: ScoreMap): Preset =>
  presetOrder.reduce<Preset>((best, candidate) => {
    if (scores[candidate] > scores[best]) return candidate;
    if (scores[candidate] === scores[best] && presetOrder.indexOf(candidate) < presetOrder.indexOf(best)) return candidate;
    return best;
  }, 'P1');

const evaluatePresetScores = (signals: LayoutSignals): ScoreMap => {
  const alertWeight = severityWeight[signals.alertsSeverity] + signals.alertsCount;
  const failureWeight = severityWeight[signals.failuresSeverity] + signals.failuresCount;

  const scores: ScoreMap = {
    P1: 4,
    P2: 0,
    P3: 0,
    P4: 0,
    P5: 0
  };

  scores.P2 += signals.approvalsPending * 2 + signals.workflowsActive;
  scores.P2 += signals.dialogueOpen ? 2 : 0;
  scores.P2 += signals.focusMode === 'review' ? 2 : 0;

  scores.P3 += alertWeight * 1.5;
  scores.P3 += signals.confidence === 'drifting' ? 3 : 0;
  scores.P3 += signals.confidence === 'unstable' ? 2 : 0;

  scores.P4 += signals.focusMode === 'focus' ? 4 : 0;
  scores.P4 += signals.dialogueOpen ? 3 : 0;
  scores.P4 += signals.remindersCount > 0 ? 1 : 0;

  scores.P5 += failureWeight * 2;
  scores.P5 += alertWeight;
  scores.P5 += signals.focusMode === 'recovery' ? 4 : 0;

  return scores;
};

export const buildAdaptiveLayoutPlan = (signals: LayoutSignals): LayoutPlan => {
  const hardRecovery =
    signals.focusMode === 'recovery' || signals.failuresSeverity === 'critical' || signals.alertsSeverity === 'critical';

  const preset = hardRecovery ? 'P5' : pickPreset(evaluatePresetScores(signals));

  let splitColumns: ColumnSplit = 'balanced';
  let activeCardId: string | undefined;

  const centerSizes: Record<string, CardPlacement['size']> = {
    system_overview: 'L',
    dialogue: 'S',
    timeline: 'M',
    world_tldr: 'S'
  };

  const rightSizes: Record<string, CardPlacement['size']> = {
    reminders: 'S',
    alerts: 'S',
    approvals: 'XS',
    workflows: 'S',
    failures: 'S'
  };

  let centerOrder = [...centerCardIds];
  let rightOrder = [...rightCardIds];

  if (preset === 'P2') {
    splitColumns = 'rightFocus';
    centerSizes.system_overview = 'M';
    centerSizes.dialogue = 'M';
    rightSizes.approvals = 'L';
    rightSizes.workflows = 'M';
    rightOrder = ['approvals', 'workflows', 'alerts', 'failures', 'reminders'];
    activeCardId = signals.approvalsPending > 0 ? 'approvals' : signals.dialogueOpen ? 'dialogue' : undefined;
  }

  if (preset === 'P3') {
    splitColumns = 'balanced';
    centerSizes.system_overview = 'M';
    centerSizes.world_tldr = 'M';
    rightSizes.alerts = 'L';
    rightOrder = ['alerts', 'failures', 'approvals', 'workflows', 'reminders'];
    activeCardId = 'alerts';
  }

  if (preset === 'P4') {
    splitColumns = 'centerFocus';
    centerSizes.dialogue = 'L';
    centerSizes.timeline = 'L';
    centerOrder = ['dialogue', 'timeline', 'system_overview', 'world_tldr'];
    rightSizes.reminders = 'XS';
    activeCardId = signals.dialogueOpen ? 'dialogue' : 'timeline';
  }

  if (preset === 'P5') {
    splitColumns = 'rightFocus';
    centerSizes.system_overview = 'M';
    centerSizes.dialogue = 'XS';
    rightSizes.failures = 'L';
    rightSizes.alerts = 'M';
    rightOrder = ['failures', 'alerts', 'approvals', 'workflows', 'reminders'];
    activeCardId = signals.failuresCount > 0 ? 'failures' : 'alerts';
  }

  if (signals.dialogueOpen && signals.focusMode !== 'recovery' && preset !== 'P5') {
    centerSizes.dialogue = centerSizes.dialogue === 'S' ? 'M' : centerSizes.dialogue;
    activeCardId ??= 'dialogue';
  }

  return {
    preset,
    splitColumns,
    generatedAt: signals.updatedAt,
    ttlSeconds: 120,
    activeCardId,
    placements: [...withPriority(centerOrder, 'center', centerSizes), ...withPriority(rightOrder, 'right', rightSizes)]
  };
};

export const mockLayoutSignals = (params: Partial<LayoutSignals>): LayoutSignals => ({
  remindersCount: 0,
  alertsCount: 0,
  alertsSeverity: 'none',
  failuresCount: 0,
  failuresSeverity: 'none',
  approvalsPending: 0,
  workflowsActive: 0,
  confidence: 'stable',
  dialogueOpen: false,
  focusMode: 'default',
  updatedAt: Date.now(),
  ...params
});

export default buildAdaptiveLayoutPlan;
