import { buildLayoutPlan } from './engine';
import { initialMockState } from '../state/mockState';

describe('widget registry layout selection', () => {
  it('always includes pinned widgets even when rule would hide them', () => {
    const state = { ...initialMockState, workflows: [], lastUserInputAt: 0 };
    const plan = buildLayoutPlan(state, ['dialogue', 'workflowsBoard']);
    const focusIds = plan.focusPlacements.map((entry) => entry.id);

    expect(focusIds).toContain('dialogue');
    expect(focusIds).toContain('workflowsBoard');
  });

  it('shows workflows board only when workflows exist or pinned', () => {
    const hiddenPlan = buildLayoutPlan({ ...initialMockState, workflows: [] }, []);
    expect(hiddenPlan.focusPlacements.map((entry) => entry.id)).not.toContain('workflowsBoard');

    const visiblePlan = buildLayoutPlan({ ...initialMockState, workflows: [] }, ['workflowsBoard']);
    expect(visiblePlan.focusPlacements.map((entry) => entry.id)).toContain('workflowsBoard');
  });
});
