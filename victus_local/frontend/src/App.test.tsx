import { fireEvent, render, screen } from '@testing-library/react';
import App from './App';

describe('Phase 4A UI', () => {
  it('renders system overview section headings', () => {
    render(<App />);

    expect(screen.getByText('System Overview')).toBeInTheDocument();
    expect(screen.getByText('TODAY')).toBeInTheDocument();
    expect(screen.getByText('UPCOMING')).toBeInTheDocument();
    expect(screen.getByText('COMPLETED')).toBeInTheDocument();
  });

  it('renders all context stack cards', () => {
    render(<App />);

    ['Reminders', 'Alerts', 'Pending Approvals', 'Active Workflows', 'Unresolved Failures'].forEach((card) => {
      expect(screen.getByText(card)).toBeInTheDocument();
    });
  });

  it('expands command dock on click', () => {
    render(<App />);

    const input = screen.getByLabelText('Command dock');
    const wrapper = input.parentElement;
    expect(wrapper).toHaveClass('w-72');

    fireEvent.click(input);
    expect(wrapper).toHaveClass('max-w-xl');
  });
});
