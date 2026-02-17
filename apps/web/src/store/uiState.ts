import { useCallback, useEffect, useMemo, useState } from 'react';
import { apiClient } from '../api/client';
import type { UIEntity, UIStateResponse } from '../api/types';
import type { AdaptiveItem } from '../engine/adaptiveScore';
import { computeAdaptiveLayout, type PinState } from '../engine/layoutEngine';

export type TimelineEvent = { id: string; label: string; detail: string; createdAt: number };

const POLL_MS_DEFAULT = 300_000;

const toAdaptiveItem = (kind: AdaptiveItem['kind'], item: UIEntity): AdaptiveItem => ({
  id: item.id,
  kind,
  title: item.title,
  detail: item.detail,
  status: item.status,
  urgency: item.urgency,
  confidenceImpact: kind === 'workflow' ? 20 : kind === 'failure' ? -35 : -10,
  severity: item.severity,
  updatedAt: item.updated_at,
  actions:
    kind === 'approval'
      ? ['approve', 'deny']
      : kind === 'reminder'
        ? ['done']
        : kind === 'workflow'
          ? ['resume', 'open']
          : ['open']
});

function stateToItems(state: UIStateResponse): AdaptiveItem[] {
  return [
    ...state.failures.map((item) => toAdaptiveItem('failure', item)),
    ...state.approvals.map((item) => toAdaptiveItem('approval', item)),
    ...state.alerts.map((item) => toAdaptiveItem('alert', item)),
    ...state.reminders.map((item) => toAdaptiveItem('reminder', item)),
    ...state.workflows.map((item) => toAdaptiveItem('workflow', item)),
    {
      id: 'dialogue-root',
      kind: 'dialogue',
      title: 'Dialogue',
      detail: state.dialogue_messages.at(-1)?.text ?? 'Victus is active.',
      status: 'active',
      urgency: 45,
      confidenceImpact: 18,
      updatedAt: state.dialogue_messages.at(-1)?.created_at ?? Date.now(),
      actions: ['open']
    },
    {
      id: 'timeline-stream',
      kind: 'timeline',
      title: 'Timeline',
      detail: 'Truth stream of system + operator actions.',
      status: 'active',
      urgency: 50,
      confidenceImpact: 12,
      updatedAt: state.timeline_events[0]?.created_at ?? Date.now(),
      actions: ['open']
    }
  ];
}

export function useUIState(pollMs = POLL_MS_DEFAULT) {
  const [apiState, setApiState] = useState<UIStateResponse | null>(null);
  const [pinState, setPinState] = useState<PinState>({});

  const refresh = useCallback(async () => {
    const next = await apiClient.getUIState();
    setApiState(next);
    return next;
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    const handle = window.setInterval(() => {
      void refresh();
    }, pollMs);
    return () => window.clearInterval(handle);
  }, [pollMs, refresh]);

  const items = useMemo(() => (apiState ? stateToItems(apiState) : []), [apiState]);
  const timelineEvents = useMemo<TimelineEvent[]>(
    () => (apiState?.timeline_events ?? []).map((event) => ({ id: event.id, label: event.label, detail: event.detail, createdAt: event.created_at })),
    [apiState]
  );

  const layout = useMemo(() => computeAdaptiveLayout(items, pinState), [items, pinState]);

  const actions = {
    approve: async (id: string) => setApiState(await apiClient.approve(id)),
    deny: async (id: string) => setApiState(await apiClient.deny(id)),
    done: async (id: string) => setApiState(await apiClient.markReminderDone(id)),
    resume: async (id: string) => setApiState(await apiClient.workflowAction(id, 'resume')),
    pause: async (id: string) => setApiState(await apiClient.workflowAction(id, 'pause')),
    advanceStep: async (id: string) => setApiState(await apiClient.workflowAction(id, 'advance_step')),
    sendCommand: async (message: string) => setApiState(await apiClient.sendDialogue(message)),
    togglePin: (id: string) => {
      setPinState((prev) => {
        if (prev[id]) {
          const next = { ...prev };
          delete next[id];
          return next;
        }
        const focusIndex = layout.focus.findIndex((card) => card.item.id === id);
        const contextIndex = layout.context.findIndex((card) => card.item.id === id);
        if (focusIndex >= 0) return { ...prev, [id]: { lane: 'focus', order: focusIndex } };
        return { ...prev, [id]: { lane: 'context', order: Math.max(0, contextIndex) } };
      });
    },
    refresh
  };

  return {
    items,
    timelineEvents,
    dialogueMessages: apiState?.dialogue_messages ?? [],
    workflows: apiState?.workflows ?? [],
    layout,
    pinState,
    actions
  };
}
