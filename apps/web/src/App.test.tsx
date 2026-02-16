import { fireEvent, render, screen, within } from '@testing-library/react';
import App from './App';

describe('phase 4B Victus lane rendering + interactivity', () => {
  it('CommandDock remains fixed in DOM', () => {
    render(<App />);

    const dockShell = screen.getByTestId('command-dock-shell');
    expect(dockShell.className).toContain('fixed');
    expect(screen.getByLabelText('Command dock')).toBeInTheDocument();
  });

  it('RightContextLane has an independent scroll container', () => {
    render(<App />);

    const scrollContainer = screen.getByTestId('right-context-scroll');
    expect(scrollContainer.className).toContain('overflow-y-auto');
  });

  it('clicking a reminder mark done mutates rendered state and updates plan output', () => {
    render(<App />);

    const reminderContextCard = screen.getByTestId('right-context-card-reminders');
    fireEvent.click(reminderContextCard);

    const firstReminder = within(reminderContextCard).getByText('Approve onboarding policy edits');
    fireEvent.click(firstReminder);

    const liveTextBefore = screen.getByText(/Active preset:/i).textContent;
    fireEvent.click(within(reminderContextCard).getByRole('button', { name: /mark done/i }));

    expect(screen.queryByText('Approve onboarding policy edits')).not.toBeInTheDocument();
    const liveTextAfter = screen.getByText(/Active preset:/i).textContent;
    expect(liveTextAfter).not.toEqual(liveTextBefore);
  });
});
