import { fireEvent, render, screen, within } from '@testing-library/react';
import App from './App';

describe('phase 4B.2 interactions', () => {
  it('approve/deny create timeline events and do not touch dialogue', () => {
    render(<App />);

    const approvalsWidget = screen.getByTestId('widget-approvals');
    fireEvent.click(within(approvalsWidget).getByRole('button', { name: 'Approve' }));

    expect(screen.getByText(/Approval resolved: Filesystem tool scope adjustment \(approved\)/)).toBeInTheDocument();
    expect(screen.queryByTestId('widget-dialogue')).not.toBeInTheDocument();
  });

  it('dialogue changes only from command submission', () => {
    render(<App />);

    expect(screen.queryByTestId('widget-dialogue')).not.toBeInTheDocument();

    const input = screen.getByLabelText('Command dock');
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: 'hello there' } });
    fireEvent.keyDown(input, { key: 'Enter' });

    expect(screen.getByTestId('widget-dialogue')).toBeInTheDocument();
    expect(screen.getByText('hello there')).toBeInTheDocument();
    expect(screen.getByText('Acknowledged: hello there')).toBeInTheDocument();
  });

  it('context lane has independent scrolling hooks', () => {
    render(<App />);

    expect(screen.getByTestId('context-stack-container').className).toContain('min-h-0');
    expect(screen.getByTestId('right-context-scroll').className).toContain('overflow-y-auto');
  });
});
