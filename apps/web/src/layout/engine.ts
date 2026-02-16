import type { MockUiState } from '../state/mockState';
import { widgetRegistry } from './widgetRegistry';
import type { FocusPlacement, LayoutEngineConfig, LayoutPlan, WidgetDefinition, WidgetId, WidgetRole } from './types';

type RuntimeWidget = Omit<WidgetDefinition, 'score'> & { score: number; pinned: boolean };

const roleWeight: Record<WidgetRole, number> = { primary: 0, secondary: 1, tertiary: 2 };

export const defaultEngineConfig: LayoutEngineConfig = {
  urgencyWeight: 0.75,
  confidenceMultiplierBase: 0.25
};

function sortByRoleThenScore(items: RuntimeWidget[]) {
  return [...items].sort((a, b) => {
    if (a.pinned !== b.pinned) return a.pinned ? -1 : 1;
    if (roleWeight[a.role] !== roleWeight[b.role]) return roleWeight[a.role] - roleWeight[b.role];
    if (a.score !== b.score) return b.score - a.score;
    return a.id.localeCompare(b.id);
  });
}

function packFocus(widgets: RuntimeWidget[]): FocusPlacement[] {
  const columns = { left: 0, right: 0 };

  return widgets.map((widget) => {
    const column = columns.left <= columns.right ? 'left' : 'right';
    columns[column] += widget.heightHint;
    return { id: widget.id, score: widget.score, role: widget.role, sizePreset: widget.sizePreset, heightHint: widget.heightHint, column };
  });
}

export function buildLayoutPlan(state: MockUiState, pinnedWidgetIds: WidgetId[] = []): LayoutPlan {
  const selected: RuntimeWidget[] = widgetRegistry
    .map((widget) => {
      const pinned = pinnedWidgetIds.includes(widget.id);
      return { ...widget, pinned, score: widget.score(state) };
    })
    .filter((widget) => widget.visibleWhen(state, widget.pinned) || widget.pinned);

  const focus = sortByRoleThenScore(selected.filter((entry) => entry.lane === 'FOCUS'));
  const context = sortByRoleThenScore(selected.filter((entry) => entry.lane === 'CONTEXT'));

  return { computedAt: Date.now(), focusPlacements: packFocus(focus), contextOrder: context.map((entry) => entry.id) };
}
