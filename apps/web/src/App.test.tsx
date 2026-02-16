import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import App from './App';
import { resetMockProviderState } from './providers/mockProvider';

describe('phase 4B.3 store/provider interactions', () => {
  beforeEach(() => {
    resetMockProviderState();
  });

  it('approve/deny create timeline events and do not touch dialogue', async () => {
    render(<App />);

    const approvalsWidget = await screen.findByTestId('widget-approvals');
    fireEvent.click(within(approvalsWidget).getByRole('button', { name: 'Approve' }));

    await waitFor(() => {
      expect(screen.getByText(/Approval resolved: Filesystem tool scope adjustment \(approved\)/)).toBeInTheDocument();
    });
    expect(screen.queryByTestId('widget-dialogue')).not.toBeInTheDocument();
  });

  it('command submit adds to dialogue thread', async () => {
    render(<App />);

    expect(screen.queryByTestId('widget-dialogue')).not.toBeInTheDocument();

    const input = await screen.findByLabelText('Command dock');
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: 'hello there' } });
    fireEvent.keyDown(input, { key: 'Enter' });

    await waitFor(() => {
      expect(screen.getByTestId('widget-dialogue')).toBeInTheDocument();
      expect(screen.getByText('hello there')).toBeInTheDocument();
      expect(screen.getByText('Acknowledged: hello there')).toBeInTheDocument();
    });
  });

  it('context lane has independent scrolling hooks', async () => {
    render(<App />);

    await screen.findByTestId('context-stack-container');
    expect(screen.getByTestId('context-stack-container').className).toContain('min-h-0');
    expect(screen.getByTestId('right-context-scroll').className).toContain('overflow-y-auto');
  });
});
