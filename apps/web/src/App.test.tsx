import { act, fireEvent, render, screen, within } from '@testing-library/react';
import App from './App';

describe('phase 4B adaptive layout interactions', () => {
  it('approve removes item, adds timeline event, and does not modify dialogue', () => {
    vi.useFakeTimers();
    render(<App />);

    const approvalsWidget = screen.getByTestId('widget-approvals');
    expect(within(approvalsWidget).getByText(/Approvals \(1\)/)).toBeInTheDocument();

    fireEvent.click(within(approvalsWidget).getByRole('button', { name: 'Approve' }));

    act(() => {
      vi.advanceTimersByTime(250);
    });

    expect(within(approvalsWidget).getByText(/Approvals \(0\)/)).toBeInTheDocument();
    expect(within(approvalsWidget).queryByText('Filesystem tool scope adjustment')).not.toBeInTheDocument();
    expect(screen.getByText(/Approval resolved: Filesystem tool scope adjustment \(approved\)/)).toBeInTheDocument();
    expect(screen.queryByTestId('widget-dialogue')).not.toBeInTheDocument();

    vi.useRealTimers();
  });

  it('clicking widget header toggles expanded state', () => {
    render(<App />);

    const timeline = screen.getByTestId('widget-timeline');
    const header = screen.getByTestId('widget-timeline-header');

    expect(timeline).toHaveAttribute('data-expanded', 'true');
    fireEvent.click(header);
    expect(timeline).toHaveAttribute('data-expanded', 'false');
    fireEvent.click(header);
    expect(timeline).toHaveAttribute('data-expanded', 'true');
  });

  it('command dock submit adds dialogue exchange and does not create approval event', () => {
    render(<App />);

    expect(screen.queryByTestId('widget-dialogue')).not.toBeInTheDocument();

    const input = screen.getByLabelText('Command dock');
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: 'hello there' } });
    fireEvent.keyDown(input, { key: 'Enter' });

    expect(screen.getByTestId('widget-dialogue')).toBeInTheDocument();
    expect(screen.getByText('hello there')).toBeInTheDocument();
    expect(screen.getByText('Acknowledged: hello there')).toBeInTheDocument();
    expect(screen.queryByText(/Approval resolved:/)).not.toBeInTheDocument();
  });

  it('context lane has min-h-0 and independent overflow container classes', () => {
    render(<App />);

    const root = screen.getByTestId('context-stack-container');
    const scroller = screen.getByTestId('right-context-scroll');

    expect(root.className).toContain('h-full');
    expect(root.className).toContain('min-h-0');
    expect(scroller.className).toContain('min-h-0');
    expect(scroller.className).toContain('overflow-y-auto');
    expect(scroller.className).toContain('flex-1');
  });
});
