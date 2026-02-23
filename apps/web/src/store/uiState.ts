import { useCallback, useEffect, useMemo, useState } from 'react';
import { apiClient } from '../api/client';
import type { DialogueMessage as ApiDialogueMessage, UIEntity, UIStateResponse } from '../api/types';
import type { AdaptiveItem } from '../engine/adaptiveScore';
import { computeAdaptiveLayout, type PinState } from '../engine/layoutEngine';
import { ApiError, orchestrateCommand } from '../lib/api';

export type TimelineEvent = { id: string; label: string; detail: string; createdAt: number };

export type CommandDialogueMessage = {
  id: string;
  role: 'user' | 'system';
  text: string;
  created_at: number;
  fields?: string[];
  candidates?: string[];
};

type ClarifyPayload = {
  error: 'clarify';
  message?: unknown;
  fields?: unknown;
  candidates?: unknown;
};

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
  const latestDialogueMessage = state.dialogue_messages[state.dialogue_messages.length - 1];

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
      detail: latestDialogueMessage?.text ?? 'Victus is active.',
      status: 'active',
      urgency: 45,
      confidenceImpact: 18,
      updatedAt: latestDialogueMessage?.created_at ?? Date.now(),
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

function toStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.filter((item): item is string => typeof item === 'string' && item.trim().length > 0);
}

function asObject(value: unknown): Record<string, unknown> | null {
  return value !== null && typeof value === 'object' ? (value as Record<string, unknown>) : null;
}

function nextLocalMessage(role: CommandDialogueMessage['role'], text: string, extras: Partial<CommandDialogueMessage> = {}): CommandDialogueMessage {
  const now = Date.now();
  return {
    id: `local-${role}-${now}-${Math.random().toString(36).slice(2, 8)}`,
    role,
    text,
    created_at: now,
    ...extras
  };
}

function toCommandDialogue(message: ApiDialogueMessage): CommandDialogueMessage {
  return {
    id: message.id,
    role: message.role,
    text: message.text,
    created_at: message.created_at
  };
}

export function useUIState(enabled = true, pollMs = POLL_MS_DEFAULT) {
  const [apiState, setApiState] = useState<UIStateResponse | null>(null);
  const [localDialogueMessages, setLocalDialogueMessages] = useState<CommandDialogueMessage[]>([]);
  const [pinState, setPinState] = useState<PinState>({});
  const [pendingClarification, setPendingClarification] = useState<{
    fields: string[];
    candidates: string[];
  } | null>(null);

  const appendDialogueMessage = useCallback((role: CommandDialogueMessage['role'], text: string, extras: Partial<CommandDialogueMessage> = {}) => {
    setLocalDialogueMessages((prev) => [...prev, nextLocalMessage(role, text, extras)]);
  }, []);

  const refresh = useCallback(async () => {
    const next = await apiClient.getUIState();
    setApiState(next);
    return next;
  }, []);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    void refresh();
  }, [enabled, refresh]);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    const handle = window.setInterval(() => {
      void refresh();
    }, pollMs);
    return () => window.clearInterval(handle);
  }, [enabled, pollMs, refresh]);

  const items = useMemo(() => (apiState ? stateToItems(apiState) : []), [apiState]);
  const dialogueMessages = useMemo(
    () => [...(apiState?.dialogue_messages ?? []).map(toCommandDialogue), ...localDialogueMessages],
    [apiState?.dialogue_messages, localDialogueMessages]
  );
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
    sendCommand: async (message: string) => {
      appendDialogueMessage('user', message);

      try {
        const response = await orchestrateCommand(message);

        if (typeof response === 'string') {
          setPendingClarification(null);
          appendDialogueMessage('system', response);
          return;
        }

        const payload = asObject(response);
        if (!payload) {
          setPendingClarification(null);
          appendDialogueMessage('system', String(response));
          return;
        }

        if (payload.error === 'clarify') {
          const clarifyPayload = payload as ClarifyPayload;
          const messageText = typeof clarifyPayload.message === 'string' ? clarifyPayload.message : 'Can you clarify what you want Victus to do?';
          const fields = toStringArray(clarifyPayload.fields);
          const candidates = toStringArray(clarifyPayload.candidates);

          setPendingClarification({ fields, candidates });
          appendDialogueMessage('system', messageText, { fields, candidates });
          return;
        }

        setPendingClarification(null);
        appendDialogueMessage('system', JSON.stringify(payload, null, 2));
      } catch (error) {
        setPendingClarification(null);

        if (error instanceof ApiError) {
          appendDialogueMessage(
            'system',
            `Request failed\nmethod: ${error.method}\nurl: ${error.url}\nstatus: ${error.status}\nresponse: ${error.bodyExcerpt}`
          );
          return;
        }

        appendDialogueMessage('system', `Request error: ${error instanceof Error ? error.message : String(error)}`);
      }
    },
    useClarificationCandidate: async (candidate: string) => {
      if (!candidate.trim()) {
        return;
      }
      await actions.sendCommand(candidate.trim());
    },
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
    dialogueMessages,
    workflows: apiState?.workflows ?? [],
    layout,
    pinState,
    pendingClarification,
    actions
  };
}
