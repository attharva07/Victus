import type { WidgetDefinition, WidgetId } from './types';

export const widgetRegistry: Record<WidgetId, WidgetDefinition> = {
  dialogue: {
    id: 'dialogue',
    lane: 'FOCUS',
    allowedSizes: ['M', 'L', 'XL'],
    defaultSize: 'L',
    minSize: 'M',
    maxSize: 'XL',
    urgency: 35,
    confidence: 80
  },
  systemOverview: {
    id: 'systemOverview',
    lane: 'FOCUS',
    allowedSizes: ['S', 'M'],
    defaultSize: 'M',
    minSize: 'S',
    maxSize: 'M',
    urgency: 40,
    confidence: 75
  },
  timeline: {
    id: 'timeline',
    lane: 'FOCUS',
    allowedSizes: ['S', 'M', 'L'],
    defaultSize: 'M',
    minSize: 'S',
    maxSize: 'L',
    urgency: 42,
    confidence: 70
  },
  healthPulse: {
    id: 'healthPulse',
    lane: 'FOCUS',
    allowedSizes: ['S', 'M'],
    defaultSize: 'S',
    minSize: 'S',
    maxSize: 'M',
    urgency: 55,
    confidence: 65,
    failureBoost: 18
  },
  reminders: {
    id: 'reminders',
    lane: 'CONTEXT',
    allowedSizes: ['M'],
    defaultSize: 'M',
    minSize: 'M',
    maxSize: 'M',
    urgency: 50,
    confidence: 64
  },
  alerts: {
    id: 'alerts',
    lane: 'CONTEXT',
    allowedSizes: ['M'],
    defaultSize: 'M',
    minSize: 'M',
    maxSize: 'M',
    urgency: 54,
    confidence: 62,
    failureBoost: 8
  },
  approvals: {
    id: 'approvals',
    lane: 'CONTEXT',
    allowedSizes: ['M'],
    defaultSize: 'M',
    minSize: 'M',
    maxSize: 'M',
    urgency: 58,
    confidence: 68,
    approvalBoost: 16
  },
  workflows: {
    id: 'workflows',
    lane: 'CONTEXT',
    allowedSizes: ['S', 'M'],
    defaultSize: 'S',
    minSize: 'S',
    maxSize: 'M',
    urgency: 38,
    confidence: 72
  },
  failures: {
    id: 'failures',
    lane: 'CONTEXT',
    allowedSizes: ['M', 'L'],
    defaultSize: 'M',
    minSize: 'M',
    maxSize: 'L',
    urgency: 60,
    confidence: 58,
    failureBoost: 22
  }
};

export const focusWidgetIds: WidgetId[] = ['dialogue', 'systemOverview', 'timeline', 'healthPulse'];
export const contextWidgetIds: WidgetId[] = ['approvals', 'failures', 'alerts', 'reminders', 'workflows'];
