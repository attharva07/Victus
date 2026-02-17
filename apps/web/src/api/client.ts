import type { UIStateResponse } from './types';

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    ...init
  });
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }
  return (await response.json()) as T;
}

export const apiClient = {
  health: () => request<{ status: string }>('/api/health'),
  getUIState: () => request<UIStateResponse>('/api/ui/state'),
  approve: (id: string) => request<UIStateResponse>(`/api/approvals/${id}/approve`, { method: 'POST' }),
  deny: (id: string) => request<UIStateResponse>(`/api/approvals/${id}/deny`, { method: 'POST' }),
  markReminderDone: (id: string) => request<UIStateResponse>(`/api/reminders/${id}/done`, { method: 'POST' }),
  workflowAction: (id: string, action: 'resume' | 'pause' | 'advance_step') =>
    request<UIStateResponse>(`/api/workflows/${id}/action`, { method: 'POST', body: JSON.stringify({ action }) }),
  sendDialogue: (message: string) => request<UIStateResponse>('/api/dialogue/send', { method: 'POST', body: JSON.stringify({ message }) })
};
