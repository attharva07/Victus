import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import App from './App';
import { apiClient } from './api/client';
import type { UIStateResponse } from './api/types';

vi.mock('./api/client', () => ({
  apiClient: {
    getUIState: vi.fn(),
    approve: vi.fn(),
    deny: vi.fn(),
    markReminderDone: vi.fn(),
    workflowAction: vi.fn(),
    sendDialogue: vi.fn()
  }
}));

const initialState: UIStateResponse = {
  reminders: [{ id: 'reminder-1', title: 'Approve onboarding policy edits', detail: 'Due today 2:00 PM', status: 'pending', urgency: 82, updated_at: 1 }],
  approvals: [{ id: 'approval-1', title: 'Filesystem tool scope adjustment', detail: 'Grant wider read/write scope for migration script.', status: 'pending', urgency: 74, updated_at: 2 }],
  alerts: [],
  failures: [],
  workflows: [{ id: 'workflow-1', title: 'Weekly planning synthesis', detail: 'Step 3/5 · 60%', status: 'paused', urgency: 60, progress: 60, step: 3, total_steps: 5, updated_at: 3 }],
  focus_lane_cards: [],
  dialogue_messages: [{ id: 'dialogue-1', role: 'system', text: 'Victus is active. Issue a command when ready.', created_at: 1 }],
  timeline_events: [{ id: 't1', label: 'Executor heartbeat stable', detail: 'Automation channels nominal.', created_at: 1 }]
};

describe('phase 4C adaptive surface', () => {
  beforeEach(() => {
    vi.mocked(apiClient.getUIState).mockResolvedValue(initialState);
    vi.mocked(apiClient.approve).mockResolvedValue({
      ...initialState,
      approvals: [],
      timeline_events: [
        { id: 't2', label: 'Approval resolved: Filesystem tool scope adjustment (approved)', detail: 'Approval approved by operator.', created_at: 5 },
        ...initialState.timeline_events
      ]
    });
    vi.mocked(apiClient.deny).mockResolvedValue(initialState);
    vi.mocked(apiClient.markReminderDone).mockResolvedValue(initialState);
    vi.mocked(apiClient.workflowAction).mockResolvedValue(initialState);
    vi.mocked(apiClient.sendDialogue).mockResolvedValue(initialState);
  });

  it('approve action triggers API call and appends timeline event', async () => {
    render(<App />);

    const approvalsWidget = await screen.findByTestId('widget-approvals');
    fireEvent.click(within(approvalsWidget).getByRole('button', { name: 'Approve' }));

    await waitFor(() => {
      expect(apiClient.approve).toHaveBeenCalledWith('approval-1');
      expect(screen.getByText(/Approval resolved: Filesystem tool scope adjustment \(approved\)/)).toBeInTheDocument();
    });
  });

  it('context lane keeps independent scrolling container', async () => {
    render(<App />);

    await screen.findByTestId('context-stack-container');
    expect(screen.getByTestId('context-stack-container').className).toContain('min-h-0');
    expect(screen.getByTestId('right-context-scroll').className).toContain('overflow-y-auto');
  });
});
