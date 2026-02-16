import { useMemo, useState } from 'react';
import type { MockUiState } from '../state/mockState';
import { buildLayoutPlan } from './engine';
import type { LayoutPlan, WidgetId } from './types';

const STORAGE_KEY = 'victus.layout.pinned';

function readPinned(): WidgetId[] {
  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw) as WidgetId[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function useLayoutEngine(state: MockUiState): {
  plan: LayoutPlan;
  pinnedWidgets: WidgetId[];
  pinWidget: (id: WidgetId) => void;
  resetLayout: () => void;
} {
  const [pinnedWidgets, setPinnedWidgets] = useState<WidgetId[]>(() => readPinned());

  const plan = useMemo(() => buildLayoutPlan(state, pinnedWidgets), [state, pinnedWidgets]);

  const pinWidget = (id: WidgetId) => {
    setPinnedWidgets((previous) => {
      const next = previous.includes(id) ? previous.filter((entry) => entry !== id) : [id, ...previous];
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      return next;
    });
  };

  const resetLayout = () => {
    window.localStorage.removeItem(STORAGE_KEY);
    setPinnedWidgets([]);
  };

  return { plan, pinnedWidgets, pinWidget, resetLayout };
}
