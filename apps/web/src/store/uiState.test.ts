import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { apiClient } from '../api/client';
import { useUIState } from './uiState';

vi.mock('../api/client', () => ({
  apiClient: {
    getUIState: vi.fn(),
    approve: vi.fn(),
    deny: vi.fn(),
    markReminderDone: vi.fn(),
    workflowAction: vi.fn()
  }
}));

const baseState = {
  failures: [],
  approvals: [{ id: 'ap-1', title: 'Approve', detail: 'detail', status: 'pending', urgency: 70, severity: 'info', updated_at: 1 }],
  alerts: [],
  reminders: [{ id: 're-1', title: 'Reminder', detail: 'soon', status: 'pending', urgency: 60, severity: 'info', updated_at: 1 }],
  workflows: [{ id: 'wf-1', title: 'Workflow', detail: 'step', status: 'paused', urgency: 55, severity: 'info', progress: 20, updated_at: 1 }],
  dialogue_messages: [],
  timeline_events: []
};

describe('uiState adaptive actions', () => {
  beforeEach(() => {
    vi.mocked(apiClient.getUIState).mockResolvedValue(baseState as never);
    vi.mocked(apiClient.approve).mockResolvedValue({ ...baseState, approvals: [] } as never);
    vi.mocked(apiClient.deny).mockResolvedValue(baseState as never);
    vi.mocked(apiClient.markReminderDone).mockResolvedValue({ ...baseState, reminders: [] } as never);
    vi.mocked(apiClient.workflowAction).mockResolvedValue({
      ...baseState,
      workflows: [{ ...baseState.workflows[0], status: 'active' }]
    } as never);
  });

  it('approve/done/resume mutate items', async () => {
    const { result } = renderHook(() => useUIState());

    await waitFor(() => {
      expect(result.current.items.find((item) => item.kind === 'approval')).toBeTruthy();
    });

    const approval = result.current.items.find((item) => item.kind === 'approval');
    const reminder = result.current.items.find((item) => item.kind === 'reminder');
    const workflow = result.current.items.find((item) => item.kind === 'workflow');

    await act(async () => {
      await result.current.actions.approve(approval!.id);
      await result.current.actions.done(reminder!.id);
      await result.current.actions.resume(workflow!.id);
    });

    expect(apiClient.approve).toHaveBeenCalledWith(approval!.id);
    expect(apiClient.markReminderDone).toHaveBeenCalledWith(reminder!.id);
    expect(apiClient.workflowAction).toHaveBeenCalledWith(workflow!.id, 'resume');
  });
});
