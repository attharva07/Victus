import { fireEvent, render, screen, within } from '@testing-library/react';
import App from './App';

describe('Phase 4B adaptive layout behavior', () => {
  it('clicking center cards toggles focus state', () => {
    render(<App />);

    const timelineCard = screen.getByTestId('stack-card-timeline');
    expect(timelineCard).toHaveAttribute('data-focused', 'false');

    fireEvent.click(timelineCard);
    expect(timelineCard).toHaveAttribute('data-focused', 'true');

    fireEvent.click(timelineCard);
    expect(timelineCard).toHaveAttribute('data-focused', 'false');
  });

  it('clicking right stack cards focuses and enables internal scroll body', () => {
    render(<App />);

    const remindersCard = screen.getByTestId('right-stack-card-reminders');
    expect(remindersCard).toHaveAttribute('data-focused', 'false');

    fireEvent.click(remindersCard);
    expect(remindersCard).toHaveAttribute('data-focused', 'true');

    const focusedBody = within(remindersCard).getByTestId('focused-rightstack-body');
    expect(focusedBody.className).toContain('overflow-y-auto');
    expect(focusedBody.className).toContain('thin-scroll');
  });

  it('command dock opens dialogue card and appends messages on enter', () => {
    render(<App />);

    const commandDock = screen.getByLabelText('Command dock');
    fireEvent.click(commandDock);

    const dialogueCard = screen.getByTestId('stack-card-dialogue');
    expect(dialogueCard).toHaveAttribute('data-focused', 'true');

    fireEvent.change(commandDock, { target: { value: 'Plan tomorrow' } });
    fireEvent.keyDown(commandDock, { key: 'Enter' });

    const dialogueThread = within(dialogueCard).getByTestId('dialogue-thread');
    expect(within(dialogueThread).getByText('Plan tomorrow')).toBeInTheDocument();
    expect(within(dialogueThread).getByText(/Acknowledged\. Captured "Plan tomorrow"/i)).toBeInTheDocument();
  });

  it('system overview does not render command log style entries', () => {
    render(<App />);

    expect(screen.queryByText(/Command:/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Submitted from Command Dock/i)).not.toBeInTheDocument();
    expect(screen.getByText('REMINDERS CREATED / UPDATED')).toBeInTheDocument();
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



  it('simulate updates preserve two-column center grid in overview', () => {
    render(<App />);

    fireEvent.click(screen.getByRole('button', { name: 'Simulate Signals Update' }));

    const grid = screen.getByTestId('center-grid');
    expect(grid.className).toContain('grid-cols-2');
  });

  it('manual focus shows Return to Adaptive control', () => {
    render(<App />);

    fireEvent.click(screen.getByTestId('stack-card-timeline'));
    expect(screen.getByRole('button', { name: 'Return to Adaptive' })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Return to Adaptive' }));
    expect(screen.queryByRole('button', { name: 'Return to Adaptive' })).not.toBeInTheDocument();
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
