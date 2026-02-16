import { fireEvent, render, screen, within } from '@testing-library/react';
import App from './App';

describe('phase 4B.1 Victus posture + density', () => {
  it('dialogue focus card uses internal scroll posture', () => {
    render(<App />);
    fireEvent.focus(screen.getByLabelText('Command dock'));

    const dialogueCard = screen.getByTestId('center-card-dialogue');
    expect(dialogueCard).toHaveAttribute('data-card-state', 'focus');

    const dialogueContent = screen.getByTestId('center-card-content-dialogue');
    expect(dialogueContent.className).toContain('overflow-y-auto');
    expect(dialogueCard.className).toContain('max-h-[55vh]');
  });

  it('health pulse renders as strip in low severity and full card in critical severity', () => {
    render(<App />);
    fireEvent.focus(screen.getByLabelText('Command dock'));

    expect(screen.getByTestId('health-pulse-strip')).toBeInTheDocument();
    expect(screen.queryByTestId('center-card-failures')).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /simulate update/i }));

    expect(screen.queryByTestId('health-pulse-strip')).not.toBeInTheDocument();
    expect(screen.getByTestId('center-card-failures')).toBeInTheDocument();
  });

  it('right panel uses one Context Stack container and keeps inline item actions', () => {
    render(<App />);

    const container = screen.getByTestId('context-stack-container');
    expect(within(container).getByText('Context Stack')).toBeInTheDocument();
    expect(within(container).getByTestId('context-stack-section-reminders')).toBeInTheDocument();

    fireEvent.click(within(container).getByText('Reminders'));
    fireEvent.click(within(container).getByText('Approve onboarding policy edits'));
    fireEvent.click(within(container).getByRole('button', { name: /mark done/i }));

    expect(screen.queryByText('Approve onboarding policy edits')).not.toBeInTheDocument();
  });

  it('command dock is collapsed by default and expands on focus', () => {
    render(<App />);

    const dockPill = screen.getByTestId('command-dock-pill');
    expect(dockPill).toHaveAttribute('data-expanded', 'false');

    fireEvent.focus(screen.getByLabelText('Command dock'));

    expect(dockPill).toHaveAttribute('data-expanded', 'true');
  });
});
