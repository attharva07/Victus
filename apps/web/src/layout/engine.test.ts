import { buildLayoutPlan, needsUrgentRecompute } from './engine';
import type { WidgetRuntimeSignals } from './types';

describe('adaptive layout engine', () => {
  const signals: WidgetRuntimeSignals = {
    dialogue: { urgency: 20, confidence: 80, role: 'secondary' },
    systemOverview: { urgency: 42, confidence: 72, role: 'secondary' },
    timeline: { urgency: 56, confidence: 70, role: 'primary' },
    healthPulse: { urgency: 48, confidence: 68, role: 'primary' },
    reminders: { urgency: 55, confidence: 62, role: 'secondary' },
    alerts: { urgency: 54, confidence: 64, role: 'secondary' },
    approvals: { urgency: 80, confidence: 66, role: 'primary' },
    workflows: { urgency: 36, confidence: 72, role: 'tertiary' },
    failures: { urgency: 58, confidence: 59, role: 'primary' }
  };

  it('is deterministic for same signals', () => {
    const a = buildLayoutPlan(signals);
    const b = buildLayoutPlan(signals);

    expect(a.focusPlacements).toEqual(b.focusPlacements);
    expect(a.contextOrder).toEqual(b.contextOrder);
  });

  it('packs focus widgets into deterministic two-column masonry', () => {
    const plan = buildLayoutPlan(signals);
    const placements = plan.focusPlacements;

    expect(placements.every((entry) => ['left', 'right'].includes(entry.column))).toBe(true);
    expect(placements[0]?.role).toBe('primary');
  });

  it('triggers urgent recompute for high urgency approvals/failures', () => {
    expect(needsUrgentRecompute({ approvals: { urgency: 90 } })).toBe(true);
    expect(needsUrgentRecompute({ failures: { urgency: 84 } })).toBe(true);
    expect(needsUrgentRecompute({ reminders: { urgency: 20 } })).toBe(false);
  });
});
