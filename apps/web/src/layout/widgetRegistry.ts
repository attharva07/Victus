import type { MockUiState } from '../state/mockState';
import type { WidgetDefinition } from './types';

const urgentReminderCount = (state: MockUiState) => state.reminders.filter((item) => item.urgency === 'high').length;
const maxFailureSeverity = (state: MockUiState) => {
  if (state.failures.some((item) => item.severity === 'critical')) return 'critical';
  if (state.failures.some((item) => item.severity === 'warning')) return 'warning';
  return 'info';
};

const scoreWithConfidence = (urgency: number, confidence: number) => urgency * 0.75 + urgency * (confidence / 100) * 0.25;

export const widgetRegistry: WidgetDefinition[] = [
  {
    id: 'dialogue', lane: 'FOCUS', role: 'primary', sizePreset: 'L', heightHint: 8, pinable: true, expandable: true,
    visibleWhen: (state, pinned) => pinned || Date.now() - state.lastUserInputAt <= 10 * 60_000,
    score: (state) => scoreWithConfidence(Date.now() - state.lastUserInputAt <= 10 * 60_000 ? 90 : 20, state.confidence)
  },
  {
    id: 'timeline', lane: 'FOCUS', role: 'secondary', sizePreset: 'M', heightHint: 6, pinable: true, expandable: true,
    visibleWhen: () => true,
    score: (state) => scoreWithConfidence(Math.min(85, 45 + state.timeline.length * 3), state.confidence)
  },
  {
    id: 'healthPulse', lane: 'FOCUS', role: 'secondary', sizePreset: 'M', heightHint: 5, pinable: true, expandable: true,
    visibleWhen: () => true,
    score: (state) => {
      const sev = maxFailureSeverity(state);
      const urgency = sev === 'critical' ? 96 : sev === 'warning' ? 82 : 42;
      return scoreWithConfidence(urgency, state.confidence);
    }
  },
  {
    id: 'systemOverview', lane: 'FOCUS', role: 'secondary', sizePreset: 'S', heightHint: 4, pinable: true, expandable: false,
    visibleWhen: () => true,
    score: (state) => scoreWithConfidence(40 + state.reminders.length + state.approvals.length + state.workflows.length, state.confidence)
  },
  {
    id: 'worldTldr', lane: 'FOCUS', role: 'tertiary', sizePreset: 'S', heightHint: 4, pinable: true, expandable: true,
    visibleWhen: (state, pinned) => pinned || state.worldTldr.length > 0,
    score: (state) => scoreWithConfidence(28 + state.worldTldr.length * 2, state.confidence)
  },
  {
    id: 'workflowsBoard', lane: 'FOCUS', role: 'secondary', sizePreset: 'M', heightHint: 5, pinable: true, expandable: true,
    visibleWhen: (state, pinned) => pinned || state.workflows.length > 0,
    score: (state) => scoreWithConfidence(Math.min(90, 30 + state.workflows.length * 20), state.confidence)
  },
  {
    id: 'remindersPanel', lane: 'FOCUS', role: 'secondary', sizePreset: 'M', heightHint: 5, pinable: true, expandable: true,
    visibleWhen: (state, pinned) => state.reminders.length > 0 && (urgentReminderCount(state) > 0 || pinned),
    score: (state) => scoreWithConfidence(35 + urgentReminderCount(state) * 22 + state.reminders.length * 4, state.confidence)
  },
  {
    id: 'approvalsPanel', lane: 'FOCUS', role: 'secondary', sizePreset: 'M', heightHint: 5, pinable: true, expandable: true,
    visibleWhen: (state, pinned) => pinned || state.approvals.length > 0,
    score: (state) => scoreWithConfidence(45 + state.approvals.length * 18, state.confidence)
  },
  {
    id: 'failures', lane: 'CONTEXT', role: 'primary', sizePreset: 'M', heightHint: 5, pinable: false, expandable: true,
    visibleWhen: () => true,
    score: (state) => scoreWithConfidence(50 + state.failures.length * 18, state.confidence)
  },
  {
    id: 'approvals', lane: 'CONTEXT', role: 'primary', sizePreset: 'M', heightHint: 5, pinable: false, expandable: true,
    visibleWhen: () => true,
    score: (state) => scoreWithConfidence(52 + state.approvals.length * 16, state.confidence)
  },
  {
    id: 'alerts', lane: 'CONTEXT', role: 'secondary', sizePreset: 'M', heightHint: 4, pinable: false, expandable: true,
    visibleWhen: () => true,
    score: (state) => scoreWithConfidence(35 + state.alerts.length * 10, state.confidence)
  },
  {
    id: 'reminders', lane: 'CONTEXT', role: 'secondary', sizePreset: 'M', heightHint: 4, pinable: false, expandable: true,
    visibleWhen: () => true,
    score: (state) => scoreWithConfidence(32 + state.reminders.length * 12, state.confidence)
  },
  {
    id: 'workflows', lane: 'CONTEXT', role: 'secondary', sizePreset: 'M', heightHint: 4, pinable: false, expandable: true,
    visibleWhen: () => true,
    score: (state) => scoreWithConfidence(30 + state.workflows.length * 12, state.confidence)
  }
];
