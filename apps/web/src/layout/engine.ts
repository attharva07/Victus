import type { MockUiState } from '../state/mockState';
import { widgetRegistry } from './widgetRegistry';
import type { FocusPinMap, FocusPlacement, LayoutEngineConfig, LayoutPlan, WidgetDefinition, WidgetRole } from './types';

type RuntimeWidget = Omit<WidgetDefinition, 'score'> & { score: number; pinned: boolean; pinMeta?: FocusPinMap[WidgetDefinition['id']] };

const roleWeight: Record<WidgetRole, number> = { primary: 0, secondary: 1, tertiary: 2 };

export const defaultEngineConfig: LayoutEngineConfig = {
  urgencyWeight: 0.75,
  confidenceMultiplierBase: 0.25
};

function sortByRoleThenScore(items: RuntimeWidget[]) {
  return [...items].sort((a, b) => {
    if (roleWeight[a.role] !== roleWeight[b.role]) return roleWeight[a.role] - roleWeight[b.role];
    if (a.score !== b.score) return b.score - a.score;
    return a.id.localeCompare(b.id);
  });
}

function sortPinnedInColumn(items: RuntimeWidget[]) {
  return [...items].sort((a, b) => {
    const anchorA = a.pinMeta?.anchor === 'top' ? 0 : 1;
    const anchorB = b.pinMeta?.anchor === 'top' ? 0 : 1;
    if (anchorA !== anchorB) return anchorA - anchorB;
    const orderA = a.pinMeta?.order ?? Number.MAX_SAFE_INTEGER;
    const orderB = b.pinMeta?.order ?? Number.MAX_SAFE_INTEGER;
    if (orderA !== orderB) return orderA - orderB;
    return a.id.localeCompare(b.id);
  });
}

function toPlacement(widget: RuntimeWidget, column: 'left' | 'right'): FocusPlacement {
  return {
    id: widget.id,
    score: widget.score,
    role: widget.role,
    sizePreset: widget.sizePreset,
    heightHint: widget.heightHint,
    column
  };
}

function packFocus(widgets: RuntimeWidget[]): FocusPlacement[] {
  const pinned = widgets.filter((entry) => entry.pinned);
  const unpinned = widgets.filter((entry) => !entry.pinned);

  const pinnedLeft = sortPinnedInColumn(pinned.filter((entry) => (entry.pinMeta?.col ?? 0) === 0));
  const pinnedRight = sortPinnedInColumn(pinned.filter((entry) => (entry.pinMeta?.col ?? 0) === 1));

  const columns = {
    left: pinnedLeft.reduce((sum, entry) => sum + entry.heightHint, 0),
    right: pinnedRight.reduce((sum, entry) => sum + entry.heightHint, 0)
  };

  const unpinnedPlacements = sortByRoleThenScore(unpinned).map((widget) => {
    const column = columns.left <= columns.right ? 'left' : 'right';
    columns[column] += widget.heightHint;
    return toPlacement(widget, column);
  });

  return [
    ...pinnedLeft.map((entry) => toPlacement(entry, 'left')),
    ...pinnedRight.map((entry) => toPlacement(entry, 'right')),
    ...unpinnedPlacements
  ];
}

export function buildLayoutPlan(state: MockUiState, pinState: FocusPinMap = {}): LayoutPlan {
  const selected: RuntimeWidget[] = widgetRegistry
    .map((widget) => {
      const pinMeta = pinState[widget.id];
      const pinned = Boolean(pinMeta?.pinned);
      return { ...widget, pinMeta, pinned, score: widget.score(state) };
    })
    .filter((widget) => widget.visibleWhen(state, widget.pinned) || widget.pinned);

  const focus = sortByRoleThenScore(selected.filter((entry) => entry.lane === 'FOCUS'));
  const context = sortByRoleThenScore(selected.filter((entry) => entry.lane === 'CONTEXT'));

  return { computedAt: Date.now(), focusPlacements: packFocus(focus), contextOrder: context.map((entry) => entry.id) };
}
