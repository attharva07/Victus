import { apiFetch } from '../lib/api';
import type { UIStateResponse } from './types';

export const apiClient = {
  health: () => apiFetch<{ status: string }>('/api/health'),
  getUIState: () => apiFetch<UIStateResponse>('/api/ui/state'),
  approve: (id: string) => apiFetch<UIStateResponse>(`/api/approvals/${id}/approve`, { method: 'POST' }),
  deny: (id: string) => apiFetch<UIStateResponse>(`/api/approvals/${id}/deny`, { method: 'POST' }),
  markReminderDone: (id: string) => apiFetch<UIStateResponse>(`/api/reminders/${id}/done`, { method: 'POST' }),
  workflowAction: (id: string, action: 'resume' | 'pause' | 'advance_step') =>
    apiFetch<UIStateResponse>(`/api/workflows/${id}/action`, { method: 'POST', body: JSON.stringify({ action }) }),
  sendDialogue: (message: string) => apiFetch<UIStateResponse>('/api/dialogue/send', { method: 'POST', body: JSON.stringify({ message }) })
};
