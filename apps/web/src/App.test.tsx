import { fireEvent, render, screen } from '@testing-library/react';
import App from './App';

describe('Phase 4A.1 stage behavior', () => {
  it('renders multiple center cards at once', () => {
    render(<App />);

    expect(screen.getByText('System Overview')).toBeInTheDocument();
    expect(screen.getByText('Timeline')).toBeInTheDocument();
    expect(screen.getByText('World TLDR')).toBeInTheDocument();
  });

  it('keyboard shift changes active card', () => {
    render(<App />);

    const stack = screen.getByLabelText('Center Card Stack');
    stack.focus();

    const systemCard = screen.getByTestId('stack-card-system_overview');
    const timelineCard = screen.getByTestId('stack-card-timeline');

    expect(systemCard).toHaveAttribute('data-active', 'true');
    expect(timelineCard).toHaveAttribute('data-active', 'false');

    fireEvent.keyDown(stack, { key: 'ArrowDown', code: 'ArrowDown' });

    expect(systemCard).toHaveAttribute('data-active', 'false');
    expect(timelineCard).toHaveAttribute('data-active', 'true');
  });

  it('expand sets focused XL card state', () => {
    render(<App />);

    fireEvent.click(screen.getAllByRole('button', { name: 'Expand' })[0]);

    expect(screen.getByRole('button', { name: 'Collapse' })).toBeInTheDocument();
    expect(screen.getByTestId('stack-card-system_overview').className).toContain('h-[72vh]');
  });

  it('command dock is always present', () => {
    render(<App />);

    const input = screen.getByLabelText('Command dock');
    expect(input).toBeInTheDocument();

    fireEvent.keyDown(screen.getByLabelText('Center Card Stack'), { key: 'ArrowDown', code: 'ArrowDown' });
    fireEvent.click(screen.getAllByRole('button', { name: 'Expand' })[0]);

    expect(screen.getByLabelText('Command dock')).toBeInTheDocument();
  });
});
