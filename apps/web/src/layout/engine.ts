import type { VictusUIState } from '../types/victus-ui';
import { widgetRegistry } from './widgetRegistry';
import type { FocusPinMap, FocusPlacement, LayoutEngineConfig, LayoutPlan, WidgetDefinition, WidgetRole } from './types';

type RuntimeWidget = Omit<WidgetDefinition, 'score'> & { score: number; pinned: boolean; pinMeta?: FocusPinMap[WidgetDefinition['id']] };

const roleWeight: Record<WidgetRole, number> = { primary: 0, secondary: 1, tertiary: 2 };

export const defaultEngineConfig: LayoutEngineConfig = { urgencyWeight: 0.75, confidenceMultiplierBase: 0.25 };

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
  return { id: widget.id, score: widget.score, role: widget.role, sizePreset: widget.sizePreset, heightHint: widget.heightHint, column };
}

function packFocus(widgets: RuntimeWidget[]): FocusPlacement[] {
  const pinned = widgets.filter((item) => item.pinned);
  const unpinned = widgets.filter((item) => !item.pinned);

  const pinnedLeft = sortPinnedInColumn(pinned.filter((entry) => entry.pinMeta?.col !== 1));
  const pinnedRight = sortPinnedInColumn(pinned.filter((entry) => entry.pinMeta?.col === 1));

  const leftPlacements = pinnedLeft.map((entry) => toPlacement(entry, 'left'));
  const rightPlacements = pinnedRight.map((entry) => toPlacement(entry, 'right'));

  const leftHeight = leftPlacements.reduce((sum, item) => sum + item.heightHint, 0);
  const rightHeight = rightPlacements.reduce((sum, item) => sum + item.heightHint, 0);

  let runningLeft = leftHeight;
  let runningRight = rightHeight;
  const unpinnedPlacements = unpinned.map((widget) => {
    const placeLeft = runningLeft <= runningRight;
    if (placeLeft) {
      runningLeft += widget.heightHint;
      return toPlacement(widget, 'left');
    }
    runningRight += widget.heightHint;
    return toPlacement(widget, 'right');
  });

  // Keep pinned cards fixed at the front of their original column.
  return [...leftPlacements, ...rightPlacements, ...unpinnedPlacements];
}

export function computeLayout(state: VictusUIState, pinState: FocusPinMap = {}, now = Date.now()): LayoutPlan {
  const selected: RuntimeWidget[] = widgetRegistry
    .map((widget) => {
      const pinMeta = pinState[widget.id];
      const pinned = Boolean(pinMeta?.pinned);
      return { ...widget, pinMeta, pinned, score: widget.score(state) };
    })
    .filter((widget) => widget.visibleWhen(state, widget.pinned) || widget.pinned);

  const focus = sortByRoleThenScore(selected.filter((entry) => entry.lane === 'FOCUS'));
  const context = sortByRoleThenScore(selected.filter((entry) => entry.lane === 'CONTEXT'));

  return { computedAt: now, focusPlacements: packFocus(focus), contextOrder: context.map((entry) => entry.id) };
}

export const buildLayoutPlan = computeLayout;
