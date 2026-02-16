import { buildLayoutPlan, needsUrgentRecompute } from './engine';
import type { WidgetRuntimeSignals } from './types';

describe('adaptive layout engine', () => {
  const signals: WidgetRuntimeSignals = {
    dialogue: { urgency: 20, confidence: 80 },
    systemOverview: { urgency: 42, confidence: 72 },
    timeline: { urgency: 56, confidence: 70 },
    healthPulse: { urgency: 48, confidence: 68 },
    reminders: { urgency: 55, confidence: 62 },
    alerts: { urgency: 54, confidence: 64 },
    approvals: { urgency: 80, confidence: 66 },
    workflows: { urgency: 36, confidence: 72 },
    failures: { urgency: 58, confidence: 59 }
  };

  it('is deterministic for same signals', () => {
    const a = buildLayoutPlan(signals);
    const b = buildLayoutPlan(signals);

    expect(a.focusPlacements).toEqual(b.focusPlacements);
    expect(a.contextOrder).toEqual(b.contextOrder);
  });

  it('packs focus widgets into deterministic rows/columns', () => {
    const plan = buildLayoutPlan(signals);
    const placements = plan.focusPlacements;

    expect(placements[0]?.colStart).toBe(1);
    expect(placements.every((entry) => entry.span <= 12)).toBe(true);
  });

  it('triggers urgent recompute for high urgency approvals/failures', () => {
    expect(needsUrgentRecompute({ approvals: { urgency: 90 } })).toBe(true);
    expect(needsUrgentRecompute({ failures: { urgency: 84 } })).toBe(true);
    expect(needsUrgentRecompute({ reminders: { urgency: 20 } })).toBe(false);
  });
});
