import { act, renderHook } from '@testing-library/react';
import { useUIState } from './uiState';

describe('uiState adaptive actions', () => {
  it('approve/deny/done/resume mutate items and append timeline events', () => {
    const { result } = renderHook(() => useUIState());

    const approval = result.current.items.find((item) => item.kind === 'approval');
    const reminder = result.current.items.find((item) => item.kind === 'reminder');
    const workflow = result.current.items.find((item) => item.kind === 'workflow');

    expect(approval).toBeTruthy();
    expect(reminder).toBeTruthy();
    expect(workflow).toBeTruthy();

    const initialEvents = result.current.timelineEvents.length;

    act(() => {
      result.current.actions.approve(approval!.id);
      result.current.actions.done(reminder!.id);
      result.current.actions.resume(workflow!.id);
    });

    expect(result.current.items.some((item) => item.id === approval!.id)).toBe(false);
    expect(result.current.items.some((item) => item.id === reminder!.id)).toBe(false);
    expect(result.current.items.find((item) => item.id === workflow!.id)?.status).toBe('active');
    expect(result.current.timelineEvents.length).toBeGreaterThanOrEqual(initialEvents + 3);
  });
});
