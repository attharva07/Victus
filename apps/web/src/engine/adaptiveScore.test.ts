import { compositeScore, confidenceSignalForItem, recencyBoost, type AdaptiveItem } from './adaptiveScore';

const baseItem: AdaptiveItem = {
  id: 'x',
  kind: 'approval',
  title: 't',
  detail: 'd',
  status: 'pending',
  urgency: 80,
  confidenceImpact: -20,
  updatedAt: Date.now(),
  actions: ['approve']
};

describe('adaptive scoring', () => {
  it('calculates composite score with weighted urgency/confidence/recency', () => {
    const now = Date.now();
    const score = compositeScore({ ...baseItem, updatedAt: now - 2 * 60_000 }, now);
    expect(score).toBeGreaterThan(70);
  });

  it('applies severity boost for critical failures', () => {
    const now = Date.now();
    const warning = compositeScore({ ...baseItem, kind: 'failure', severity: 'warning', confidenceImpact: -30 }, now);
    const critical = compositeScore({ ...baseItem, kind: 'failure', severity: 'critical', confidenceImpact: -30 }, now);
    expect(critical).toBeGreaterThan(warning);
  });

  it('recency and confidence helpers stay bounded', () => {
    expect(confidenceSignalForItem({ ...baseItem, confidenceImpact: -200 })).toBeLessThanOrEqual(100);
    expect(recencyBoost({ ...baseItem, updatedAt: Date.now() - 1000 * 60 * 60 * 20 })).toBeGreaterThanOrEqual(10);
  });
});
