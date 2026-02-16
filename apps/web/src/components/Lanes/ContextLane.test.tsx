import { render, screen } from '@testing-library/react';
import ContextLane from './ContextLane';
import { AlertsWidget, ApprovalsWidget, FailuresWidget, RemindersWidget, WorkflowsWidget } from '../widgets/ContextWidgets';
import { initialMockState } from '../../state/mockState';
import type { WidgetId } from '../../layout/types';

const renderMap: Record<WidgetId, JSX.Element> = {
  failures: <FailuresWidget items={initialMockState.failures} />,
  approvals: <ApprovalsWidget items={[]} onApprove={() => undefined} onDeny={() => undefined} />,
  alerts: <AlertsWidget items={initialMockState.alerts} />,
  reminders: <RemindersWidget items={[]} />,
  workflows: <WorkflowsWidget items={[]} />,
  dialogue: <></>,
  timeline: <></>,
  healthPulse: <></>,
  systemOverview: <></>,
  worldTldr: <></>,
  workflowsBoard: <></>,
  remindersPanel: <></>,
  approvalsPanel: <></>
};

describe('context stack scroll layout', () => {
  it('renders a single scroll container in the right pane', () => {
    render(
      <ContextLane
        orderedIds={['failures', 'approvals', 'alerts', 'reminders', 'workflows']}
        renderWidget={(id) => renderMap[id]}
      />
    );

    const container = screen.getByTestId('context-stack-container');
    const scrollableNodes = container.querySelectorAll('.overflow-y-auto');

    expect(scrollableNodes).toHaveLength(1);
    expect(screen.getByTestId('right-context-scroll').className).toContain('h-full');
    expect(screen.getByText('No reminders right now.')).toBeInTheDocument();
  });
});
