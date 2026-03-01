import { mockProvider, resetMockProviderState } from '../providers/mockProvider';

describe('mock provider transitions', () => {
  beforeEach(() => {
    resetMockProviderState();
  });

  it('approval resolution updates timeline but leaves dialogue unchanged', async () => {
    const before = await mockProvider.getState();
    const next = await mockProvider.decideApproval('ap-1', 'denied');

    expect(next.contextGroups.approvals).toHaveLength(0);
    expect(next.timeline.today[0]?.label).toMatch(/Approval resolved: .*\(denied\)/);
    expect(next.dialogue.messages).toEqual(before.dialogue.messages);
  });

  it('dialogue only changes from command submission helper', async () => {
    const before = await mockProvider.getState();
    const same = await mockProvider.decideApproval('missing', 'approved');
    expect(same.dialogue.messages).toEqual(before.dialogue.messages);

    const submitted = await mockProvider.submitCommand('sync tasks');
    expect(submitted.dialogue.messages.length).toBeGreaterThan(before.dialogue.messages.length);
    expect(submitted.dialogue.messages[submitted.dialogue.messages.length - 2]?.text).toBe('sync tasks');
  });
});
