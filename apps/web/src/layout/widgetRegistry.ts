import type { VictusUIState } from '../types/victus-ui';
import type { WidgetDefinition } from './types';

const urgentReminderCount = (state: VictusUIState) => state.contextGroups.reminders.filter((item) => item.urgency === 'high').length;
const maxFailureSeverity = (state: VictusUIState) => {
  if (state.contextGroups.failures.some((item) => item.severity === 'critical')) return 'critical';
  if (state.contextGroups.failures.some((item) => item.severity === 'warning')) return 'warning';
  return 'info';
};

const scoreWithConfidence = (urgency: number, confidence: number) => urgency * 0.75 + urgency * (confidence / 100) * 0.25;

export const widgetRegistry: WidgetDefinition[] = [
  { id: 'dialogue', lane: 'FOCUS', role: 'primary', sizePreset: 'L', heightHint: 8, pinable: true, expandable: true,
    visibleWhen: (state, pinned) => pinned || Date.now() - state.lastUserInputAt <= 10 * 60_000,
    score: (state) => scoreWithConfidence(Date.now() - state.lastUserInputAt <= 10 * 60_000 ? 90 : 20, state.bottomStrip.confidence) },
  { id: 'timeline', lane: 'FOCUS', role: 'secondary', sizePreset: 'M', heightHint: 6, pinable: true, expandable: true,
    visibleWhen: () => true,
    score: (state) => scoreWithConfidence(Math.min(85, 45 + state.timeline.today.length + state.timeline.upcoming.length + state.timeline.completed.length), state.bottomStrip.confidence) },
  { id: 'healthPulse', lane: 'FOCUS', role: 'secondary', sizePreset: 'M', heightHint: 5, pinable: true, expandable: true,
    visibleWhen: () => true,
    score: (state) => {
      const sev = maxFailureSeverity(state);
      const urgency = sev === 'critical' ? 96 : sev === 'warning' ? 82 : 42;
      return scoreWithConfidence(urgency, state.bottomStrip.confidence);
    } },
  { id: 'systemOverview', lane: 'FOCUS', role: 'secondary', sizePreset: 'S', heightHint: 4, pinable: true, expandable: false,
    visibleWhen: () => true,
    score: (state) => scoreWithConfidence(40 + state.contextGroups.reminders.length + state.contextGroups.approvals.length + state.contextGroups.workflows.length, state.bottomStrip.confidence) },
  { id: 'worldTldr', lane: 'FOCUS', role: 'tertiary', sizePreset: 'S', heightHint: 4, pinable: true, expandable: true,
    visibleWhen: (state, pinned) => pinned || state.worldTldr.length > 0,
    score: (state) => scoreWithConfidence(28 + state.worldTldr.length * 2, state.bottomStrip.confidence) },
  { id: 'workflowsBoard', lane: 'FOCUS', role: 'secondary', sizePreset: 'M', heightHint: 5, pinable: true, expandable: true,
    visibleWhen: (state, pinned) => pinned || state.contextGroups.workflows.length > 0,
    score: (state) => scoreWithConfidence(Math.min(90, 30 + state.contextGroups.workflows.length * 20), state.bottomStrip.confidence) },
  { id: 'remindersPanel', lane: 'FOCUS', role: 'secondary', sizePreset: 'M', heightHint: 5, pinable: true, expandable: true,
    visibleWhen: (state, pinned) => state.contextGroups.reminders.length > 0 && (urgentReminderCount(state) > 0 || pinned),
    score: (state) => scoreWithConfidence(35 + urgentReminderCount(state) * 22 + state.contextGroups.reminders.length * 4, state.bottomStrip.confidence) },
  { id: 'approvalsPanel', lane: 'FOCUS', role: 'secondary', sizePreset: 'M', heightHint: 5, pinable: true, expandable: true,
    visibleWhen: (state, pinned) => pinned || state.contextGroups.approvals.length > 0,
    score: (state) => scoreWithConfidence(45 + state.contextGroups.approvals.length * 18, state.bottomStrip.confidence) },
  { id: 'failures', lane: 'CONTEXT', role: 'primary', sizePreset: 'M', heightHint: 5, pinable: false, expandable: true,
    visibleWhen: () => true,
    score: (state) => scoreWithConfidence(50 + state.contextGroups.failures.length * 18, state.bottomStrip.confidence) },
  { id: 'approvals', lane: 'CONTEXT', role: 'primary', sizePreset: 'M', heightHint: 5, pinable: false, expandable: true,
    visibleWhen: () => true,
    score: (state) => scoreWithConfidence(52 + state.contextGroups.approvals.length * 16, state.bottomStrip.confidence) },
  { id: 'alerts', lane: 'CONTEXT', role: 'secondary', sizePreset: 'M', heightHint: 4, pinable: false, expandable: true,
    visibleWhen: () => true,
    score: (state) => scoreWithConfidence(35 + state.contextGroups.alerts.length * 10, state.bottomStrip.confidence) },
  { id: 'reminders', lane: 'CONTEXT', role: 'secondary', sizePreset: 'M', heightHint: 4, pinable: false, expandable: true,
    visibleWhen: () => true,
    score: (state) => scoreWithConfidence(32 + state.contextGroups.reminders.length * 12, state.bottomStrip.confidence) },
  { id: 'workflows', lane: 'CONTEXT', role: 'secondary', sizePreset: 'M', heightHint: 4, pinable: false, expandable: true,
    visibleWhen: () => true,
    score: (state) => scoreWithConfidence(30 + state.contextGroups.workflows.length * 12, state.bottomStrip.confidence) }
];
