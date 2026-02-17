import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import App from './App';

describe('phase 4C adaptive surface', () => {
  it('approve action removes approval and appends timeline event', async () => {
    render(<App />);

    const approvalsWidget = await screen.findByTestId('widget-approvals');
    fireEvent.click(within(approvalsWidget).getByRole('button', { name: 'Approve' }));

    await waitFor(() => {
      expect(screen.getByText(/Approval resolved: Filesystem tool scope adjustment \(approved\)/)).toBeInTheDocument();
    });
  });

  it('timeline stream is always visible in overview', async () => {
    render(<App />);
    expect(await screen.findByTestId('widget-timeline')).toBeInTheDocument();
  });

  it('context lane keeps independent scrolling container', async () => {
    render(<App />);

    await screen.findByTestId('context-stack-container');
    expect(screen.getByTestId('context-stack-container').className).toContain('min-h-0');
    expect(screen.getByTestId('right-context-scroll').className).toContain('overflow-y-auto');
  });
});
