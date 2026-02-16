import { fireEvent, render, screen, within } from '@testing-library/react';
import App from './App';

describe('Phase 4A.2 behavior', () => {
  it('right stack focus mode enables internal scroll container and shows collapse controls', () => {
    render(<App />);

    const remindersLabel = screen.getByRole('button', { name: 'Reminders' });
    const remindersCard = remindersLabel.closest('section');
    expect(remindersCard).toBeTruthy();

    const expandButton = within(remindersCard as HTMLElement).getByRole('button', { name: 'Expand' });
    fireEvent.click(expandButton);

    expect(screen.getByRole('button', { name: /collapse/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /back/i })).toBeInTheDocument();

    const focusedBody = screen.getByTestId('focused-rightstack-body');
    expect(focusedBody.className).toContain('overflow-y-auto');
    expect(focusedBody.className).toContain('thin-scroll');
  });

  it('left rail navigation switches to memories view and renders search input', () => {
    render(<App />);

    fireEvent.click(screen.getByRole('button', { name: 'Memories' }));

    expect(screen.getByLabelText('Search memories')).toBeInTheDocument();
  });

  it('memories search filters list', () => {
    render(<App />);

    fireEvent.click(screen.getByRole('button', { name: 'Memories' }));
    fireEvent.change(screen.getByLabelText('Search memories'), { target: { value: 'incident' } });

    expect(screen.getByText('Infra incident follow-up')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Q2 Planning Principles/i })).not.toBeInTheDocument();
  });

  it('finance add transaction appends to list', () => {
    render(<App />);

    fireEvent.click(screen.getByRole('button', { name: 'Finance' }));

    fireEvent.change(screen.getByLabelText('Transaction label'), { target: { value: 'Book sale' } });
    fireEvent.change(screen.getByLabelText('Transaction amount'), { target: { value: '45' } });
    fireEvent.change(screen.getByLabelText('Transaction type'), { target: { value: 'income' } });
    fireEvent.click(screen.getByRole('button', { name: 'Add transaction' }));

    expect(screen.getByText('Book sale')).toBeInTheDocument();
    expect(screen.getByText('4 entries')).toBeInTheDocument();
  });
});
