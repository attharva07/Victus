import { act, fireEvent, render, screen, within } from '@testing-library/react';
import App from './App';

describe('phase 4B.2 interactions + transitions + command dock', () => {
  it('clicking center card header expands and clicking again collapses', () => {
    render(<App />);

    const timelineCard = screen.getByTestId('center-card-timeline');
    const timelineHeader = screen.getByTestId('center-card-header-timeline');

    expect(timelineCard).toHaveAttribute('data-card-state', 'peek');

    fireEvent.click(timelineHeader);
    expect(timelineCard).toHaveAttribute('data-card-state', 'focus');

    fireEvent.click(timelineHeader);
    expect(timelineCard).toHaveAttribute('data-card-state', 'peek');
  });

  it('clicking a button inside card does not collapse it', () => {
    render(<App />);

    const timelineCard = screen.getByTestId('center-card-timeline');
    const timelineHeader = screen.getByTestId('center-card-header-timeline');

    fireEvent.click(timelineHeader);
    expect(timelineCard).toHaveAttribute('data-card-state', 'focus');

    fireEvent.click(screen.getByRole('button', { name: /simulate update/i }));
    expect(timelineCard).toHaveAttribute('data-card-state', 'focus');
  });

  it('approve removes approval item and adds timeline system event', () => {
    vi.useFakeTimers();
    render(<App />);

    const container = screen.getByTestId('context-stack-container');
    fireEvent.click(within(container).getByText('Approvals'));

    expect(within(container).getByText('Filesystem tool scope adjustment')).toBeInTheDocument();
    fireEvent.click(within(container).getByRole('button', { name: 'Approve' }));

    act(() => {
      vi.advanceTimersByTime(250);
    });

    expect(within(container).queryByText('Filesystem tool scope adjustment')).not.toBeInTheDocument();

    const timelineCard = screen.queryByTestId('center-card-timeline');
    if (timelineCard) {
      fireEvent.click(screen.getByTestId('center-card-header-timeline'));
      expect(screen.getByText('Just now · Approval resolved: Filesystem tool scope adjustment (approved)')).toBeInTheDocument();
    }

    vi.useRealTimers();
  });

  it('command dock expands on Ctrl+K, submits on Enter, and applies Escape rules', () => {
    vi.useFakeTimers();
    render(<App />);

    const dockPill = screen.getByTestId('command-dock-pill');
    const input = screen.getByLabelText('Command dock');

    expect(dockPill).toHaveAttribute('data-expanded', 'false');

    fireEvent.keyDown(window, { key: 'k', ctrlKey: true });
    expect(dockPill).toHaveAttribute('data-expanded', 'true');

    fireEvent.change(input, { target: { value: 'Route context to finance' } });
    fireEvent.keyDown(input, { key: 'Enter' });

    expect(screen.getByText('Route context to finance')).toBeInTheDocument();
    expect(screen.getByText('Command accepted: Route context to finance')).toBeInTheDocument();
    expect((input as HTMLInputElement).value).toBe('');

    act(() => {
      vi.advanceTimersByTime(3000);
    });

    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: 'keep open' } });
    fireEvent.keyDown(input, { key: 'Escape' });
    expect((input as HTMLInputElement).value).toBe('');
    expect(dockPill).toHaveAttribute('data-expanded', 'true');

    fireEvent.keyDown(input, { key: 'Escape' });
    expect(dockPill).toHaveAttribute('data-expanded', 'false');

    vi.useRealTimers();
  });
});
