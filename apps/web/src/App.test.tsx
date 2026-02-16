import { fireEvent, render, screen, within } from '@testing-library/react';
import App from './App';

describe('Phase 4A.1 interactive UI', () => {
  it('opens detail drawer when clicking timeline item', () => {
    render(<App />);

    fireEvent.click(screen.getByRole('button', { name: /Review deployment checklist/i }));

    expect(screen.getByText('Item Details')).toBeInTheDocument();
    expect(screen.getAllByText('Review deployment checklist').length).toBeGreaterThan(1);
  });

  it('close button returns to context stack', () => {
    render(<App />);

    fireEvent.click(screen.getByRole('button', { name: /Review deployment checklist/i }));
    fireEvent.click(screen.getByRole('button', { name: /Close details/i }));

    expect(screen.getByText('Reminders')).toBeInTheDocument();
  });

  it('mark done moves an item to completed', () => {
    render(<App />);

    fireEvent.click(screen.getByRole('button', { name: /Review deployment checklist/i }));
    fireEvent.click(screen.getByRole('button', { name: 'Mark Done' }));

    const completedSection = screen.getByText('COMPLETED').closest('section');
    expect(completedSection).not.toBeNull();
    expect(within(completedSection as HTMLElement).getByText('Review deployment checklist')).toBeInTheDocument();
  });

  it('submitting command dock creates a new today item', () => {
    render(<App />);

    const input = screen.getByLabelText('Command dock');
    fireEvent.change(input, { target: { value: 'run digest' } });
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });

    expect(screen.getByText('Command: run digest')).toBeInTheDocument();
  });

  it('left rail switches to placeholder views', () => {
    render(<App />);

    fireEvent.click(screen.getByRole('button', { name: 'Finance' }));

    expect(screen.getByText('Finance')).toBeInTheDocument();
    expect(screen.getByText(/Coming soon/i)).toBeInTheDocument();
  });
});
