import { useCallback, useEffect, useMemo, useState } from 'react';
import { buildLayoutPlan, defaultEngineConfig, needsUrgentRecompute } from './engine';
import type { LayoutEngineConfig, LayoutPlan, WidgetId, WidgetRuntimeSignals } from './types';

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

export function useLayoutEngine({
  signals,
  config,
  devMode = false
}: {
  signals: WidgetRuntimeSignals;
  config?: Partial<LayoutEngineConfig>;
  devMode?: boolean;
}): {
  plan: LayoutPlan;
  pinnedWidgets: WidgetId[];
  pinWidget: (id: WidgetId) => void;
  resetLayout: () => void;
} {
  const mergedConfig = useMemo(() => ({ ...defaultEngineConfig, ...config }), [config]);
  const [pinnedWidgets, setPinnedWidgets] = useState<WidgetId[]>(() => readPinned());

  const composedSignals = useMemo<WidgetRuntimeSignals>(() => {
    const next: WidgetRuntimeSignals = { ...signals };
    pinnedWidgets.forEach((id) => {
      next[id] = { ...(next[id] ?? {}), pinned: true };
    });
    return next;
  }, [pinnedWidgets, signals]);

  const [plan, setPlan] = useState<LayoutPlan>(() => buildLayoutPlan(composedSignals, mergedConfig));

  const recompute = useCallback(() => {
    setPlan(buildLayoutPlan(composedSignals, mergedConfig));
  }, [composedSignals, mergedConfig]);

  useEffect(() => {
    recompute();
  }, [recompute]);

  useEffect(() => {
    if (import.meta.env.MODE === 'test') {
      return undefined;
    }

    const id = window.setInterval(() => {
      setPlan(buildLayoutPlan(composedSignals, mergedConfig));
    }, mergedConfig.recomputeIntervalMs);

    return () => window.clearInterval(id);
  }, [composedSignals, mergedConfig]);

  useEffect(() => {
    if (needsUrgentRecompute(composedSignals, mergedConfig)) {
      recompute();
    }
  }, [composedSignals, mergedConfig, recompute]);

  const pinWidget = (id: WidgetId) => {
    setPinnedWidgets((previous) => {
      if (previous.includes(id)) {
        const next = previous.filter((entry) => entry !== id);
        window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
        return next;
      }

      const next = [id, ...previous];
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      return next;
    });
  };

  const resetLayout = () => {
    if (!devMode) return;
    window.localStorage.removeItem(STORAGE_KEY);
    setPinnedWidgets([]);
  };

  return { plan, pinnedWidgets, pinWidget, resetLayout };
}
