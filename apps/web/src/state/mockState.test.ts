import { applyApprovalDecision, initialMockState, submitCommand } from './mockState';

describe('mock state transitions', () => {
  it('approval resolution updates timeline but leaves dialogue unchanged', () => {
    const next = applyApprovalDecision(initialMockState, 'ap-1', 'denied');
    expect(next.approvals).toHaveLength(0);
    expect(next.timeline[0]?.label).toMatch(/Approval resolved: .*\(denied\)/);
    expect(next.dialogue).toEqual(initialMockState.dialogue);
  });

  it('dialogue only changes from command submission helper', () => {
    const same = applyApprovalDecision(initialMockState, 'missing', 'approved');
    expect(same.dialogue).toEqual(initialMockState.dialogue);

    const submitted = submitCommand(initialMockState, 'sync tasks');
    expect(submitted.dialogue.length).toBeGreaterThan(initialMockState.dialogue.length);
    expect(submitted.dialogue[submitted.dialogue.length - 2]?.text).toBe('sync tasks');
  });
});
