import { useEffect, useMemo, useState } from 'react';
import type { VictusUIState } from '../types/victus-ui';
import { computeLayout } from './engine';
import type { FocusPinMap, FocusPlacement, LayoutPlan, WidgetId } from './types';

const STORAGE_KEY = 'victus.layout.focusPins';

function readPins(): FocusPinMap {
  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (!raw) return {};
  try {
    const parsed = JSON.parse(raw) as FocusPinMap | WidgetId[];
    if (Array.isArray(parsed)) {
      return parsed.reduce<FocusPinMap>((acc, id, index) => {
        acc[id] = { pinned: true, col: 0, order: index, anchor: 'normal' };
        return acc;
      }, {});
    }
    return parsed && typeof parsed === 'object' ? parsed : {};
  } catch {
    return {};
  }
}

function getPlacementHint(id: WidgetId, placements: FocusPlacement[]): { col: 0 | 1; order: number } {
  const placement = placements.find((entry) => entry.id === id);
  const col: 0 | 1 = placement?.column === 'right' ? 1 : 0;
  const colOrder = placements.filter((entry) => (entry.column === 'right' ? 1 : 0) === col).findIndex((entry) => entry.id === id);
  return { col, order: colOrder >= 0 ? colOrder : placements.length };
}

export function useLayoutEngine(state: VictusUIState | null): { plan: LayoutPlan; pinnedWidgets: WidgetId[]; pinWidget: (id: WidgetId) => void; resetLayout: () => void } {
  const [pinState, setPinState] = useState<FocusPinMap>(() => readPins());
  const [tick, setTick] = useState(0);

  useEffect(() => {
    const interval = window.setInterval(() => setTick((current) => current + 1), 15000);
    return () => window.clearInterval(interval);
  }, []);

  const plan = useMemo(() => {
    if (!state) return { computedAt: Date.now(), focusPlacements: [], contextOrder: [] };
    return computeLayout(state, pinState, Date.now() + tick);
  }, [state, pinState, tick]);

  const pinWidget = (id: WidgetId) => {
    setPinState((previous) => {
      const hint = getPlacementHint(id, plan.focusPlacements);
      const current = previous[id];
      const next: FocusPinMap = {
        ...previous,
        [id]: { pinned: !current?.pinned, col: current?.col ?? hint.col, order: current?.order ?? hint.order, anchor: current?.anchor ?? 'normal' }
      };
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      return next;
    });
  };

  const resetLayout = () => {
    window.localStorage.removeItem(STORAGE_KEY);
    setPinState({});
  };

  const pinnedWidgets = Object.entries(pinState).filter(([, meta]) => Boolean(meta?.pinned)).map(([id]) => id as WidgetId);
  return { plan, pinnedWidgets, pinWidget, resetLayout };
}
