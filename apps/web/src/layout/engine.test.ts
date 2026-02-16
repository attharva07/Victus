import { buildLayoutPlan } from './engine';
import { initialMockProviderState } from '../providers/mockProvider';

describe('widget registry layout selection', () => {
  it('always includes pinned widgets even when rule would hide them', () => {
    const state = { ...initialMockProviderState, contextGroups: { ...initialMockProviderState.contextGroups, workflows: [] }, lastUserInputAt: 0 };
    const plan = buildLayoutPlan(state, {
      dialogue: { pinned: true, col: 0, order: 0, anchor: 'normal' },
      workflowsBoard: { pinned: true, col: 1, order: 0, anchor: 'normal' }
    });
    const focusIds = plan.focusPlacements.map((entry) => entry.id);

    expect(focusIds).toContain('dialogue');
    expect(focusIds).toContain('workflowsBoard');
  });

  it('shows workflows board only when workflows exist or pinned', () => {
    const hiddenPlan = buildLayoutPlan({ ...initialMockProviderState, contextGroups: { ...initialMockProviderState.contextGroups, workflows: [] } }, {});
    expect(hiddenPlan.focusPlacements.map((entry) => entry.id)).not.toContain('workflowsBoard');

    const visiblePlan = buildLayoutPlan({ ...initialMockProviderState, contextGroups: { ...initialMockProviderState.contextGroups, workflows: [] } }, {
      workflowsBoard: { pinned: true, col: 0, order: 0, anchor: 'normal' }
    });
    expect(visiblePlan.focusPlacements.map((entry) => entry.id)).toContain('workflowsBoard');
  });

  it('keeps an already pinned widget in its original column when another widget is pinned later', () => {
    const firstPinPlan = buildLayoutPlan(initialMockProviderState, {
      timeline: { pinned: true, col: 1, order: 0, anchor: 'normal' }
    });

    const firstPinned = firstPinPlan.focusPlacements.find((entry) => entry.id === 'timeline');
    expect(firstPinned?.column).toBe('right');

    const secondPinPlan = buildLayoutPlan(initialMockProviderState, {
      timeline: { pinned: true, col: 1, order: 0, anchor: 'normal' },
      dialogue: { pinned: true, col: 0, order: 0, anchor: 'normal' }
    });

    const timelinePlacement = secondPinPlan.focusPlacements.find((entry) => entry.id === 'timeline');
    expect(timelinePlacement?.column).toBe('right');
  });
});
