import { FormEvent, useEffect, useMemo, useState } from 'react';
import BottomStatusStrip from './components/BottomStrip';
import CommandDock from './components/CommandDock';
import ContextLane from './components/Lanes/ContextLane';
import FocusLane from './components/Lanes/FocusLane';
import LeftRail, { type VictusView } from './components/LeftRail';
import { AlertsWidget, ApprovalsWidget, FailuresWidget, RemindersWidget, WorkflowsWidget } from './components/widgets/ContextWidgets';
import { DialogueWidget, TimelineWidget } from './components/widgets/FocusWidgets';
import type { AdaptiveItem } from './engine/adaptiveScore';
import {
  ApiError,
  bootstrapInit,
  bootstrapStatus,
  cameraStatus,
  filesList,
  financeSummary,
  getToken,
  login,
  memoriesList,
  setToken,
  validateStoredToken
} from './lib/api';
import { useUIState } from './store/uiState';
import CameraScreen from './views/CameraScreen';
import FilesScreen from './views/FilesScreen';
import FinanceScreen from './views/FinanceScreen';
import MemoriesScreen from './views/MemoriesScreen';

function byKind(items: AdaptiveItem[], kind: AdaptiveItem['kind']) {
  return items.filter((item) => item.kind === kind);
}

function toErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return `(${error.status}) ${error.method} ${error.path}: ${error.bodyExcerpt}`;
  }
  return error instanceof Error ? error.message : String(error);
}

export default function App() {
  const [activeView, setActiveView] = useState<VictusView>('overview');
  const [bootstrapped, setBootstrapped] = useState<boolean | null>(null);
  const [authReady, setAuthReady] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');
  const [username, setUsername] = useState((import.meta.env.VITE_TEST_USERNAME ?? 'admin').trim() || 'admin');
  const [password, setPassword] = useState((import.meta.env.VITE_TEST_PASSWORD ?? '').trim());
  const [loading, setLoading] = useState(false);

  const [memoriesData, setMemoriesData] = useState<unknown[] | null>(null);
  const [financeData, setFinanceData] = useState<unknown | null>(null);
  const [filesData, setFilesData] = useState<string[] | null>(null);
  const [cameraData, setCameraData] = useState<unknown | null>(null);
  const [viewErrors, setViewErrors] = useState<Partial<Record<VictusView, string>>>({});

  const { items, timelineEvents, dialogueMessages, workflows, layout, pinState, pendingClarification, actions } = useUIState(authReady);

  useEffect(() => {
    const checkBootstrap = async () => {
      try {
        const status = await bootstrapStatus();
        setBootstrapped(status.bootstrapped);
        if (!status.bootstrapped) {
          setAuthReady(false);
          setStatusMessage('Backend needs bootstrap initialization.');
          return;
        }

        const hasStoredToken = Boolean(getToken());
        if (!hasStoredToken) {
          setAuthReady(false);
          setStatusMessage('Backend bootstrap complete. Please log in.');
          return;
        }

        const tokenIsValid = await validateStoredToken();
        setAuthReady(tokenIsValid);
        setStatusMessage(tokenIsValid ? 'Backend bootstrap complete.' : 'Stored session expired. Please log in again.');
      } catch (error) {
        setAuthReady(false);
        setStatusMessage(`Failed to check bootstrap: ${toErrorMessage(error)}`);
      }
    };

    void checkBootstrap();
  }, []);

  useEffect(() => {
    const loadViewData = async () => {
      if (!authReady) {
        return;
      }
      try {
        if (activeView === 'memories') {
          const response = await memoriesList();
          setMemoriesData(response.results);
        }
        if (activeView === 'finance') {
          const response = await financeSummary();
          setFinanceData(response.report);
        }
        if (activeView === 'files') {
          const response = await filesList();
          setFilesData(response.files);
        }
        if (activeView === 'camera') {
          const response = await cameraStatus();
          setCameraData(response);
        }
      } catch (error) {
        if (error instanceof ApiError && error.status === 404) {
          setViewErrors((prev) => ({ ...prev, [activeView]: 'Not implemented server-side.' }));
          return;
        }
        const message = `Failed to load ${activeView}: ${toErrorMessage(error)}`;
        setViewErrors((prev) => ({ ...prev, [activeView]: message }));
        setStatusMessage(message);
      }
    };

    void loadViewData();
  }, [activeView, authReady]);

  const grouped = useMemo(
    () => ({
      failures: byKind(items, 'failure'),
      approvals: byKind(items, 'approval'),
      alerts: byKind(items, 'alert'),
      reminders: byKind(items, 'reminder'),
      workflows: byKind(items, 'workflow'),
      dialogue: byKind(items, 'dialogue')[0]
    }),
    [items]
  );

  const renderContextWidget = (kindId: string) => {
    if (kindId === 'failure') return <FailuresWidget items={grouped.failures.map((i) => ({ id: i.id, title: i.title, severity: i.severity ?? 'info', ageMinutes: 0 }))} />;
    if (kindId === 'approval') return <ApprovalsWidget items={grouped.approvals.map((i) => ({ id: i.id, title: i.title, detail: i.detail, requestedBy: 'Operator' }))} onApprove={(id) => void actions.approve(id)} onDeny={(id) => void actions.deny(id)} />;
    if (kindId === 'alert') return <AlertsWidget items={grouped.alerts.map((i) => ({ id: i.id, title: i.title, detail: i.detail }))} />;
    if (kindId === 'reminder') return <RemindersWidget items={grouped.reminders.map((i) => ({ id: i.id, title: i.title, due: i.detail, urgency: 'high' }))} onDone={(id) => void actions.done(id)} />;
    if (kindId === 'workflow') return <WorkflowsWidget items={grouped.workflows.map((i) => ({ id: i.id, title: i.title, progress: workflows.find((w) => w.id === i.id)?.progress ?? 0, stepLabel: i.detail, resumable: true }))} onResume={(id) => void actions.resume(id)} onPause={(id) => void actions.pause(id)} onAdvanceStep={(id) => void actions.advanceStep(id)} />;
    return null;
  };

  const focusPlacements = layout.focus.map((card, index) => ({
    id: card.item.id,
    score: card.score,
    role: 'secondary' as const,
    sizePreset: card.size === 'FULL' ? 'L' : card.size === 'XL' ? 'L' : card.size,
    heightHint: card.size === 'XL' ? 4 : card.size === 'L' ? 3 : 2,
    column: (index % 2 === 0 ? 'left' : 'right') as 'left' | 'right'
  }));

  const contextOrder = Array.from(new Set(layout.context.map((card) => card.item.kind)));

  const renderFocusWidget = (id: string) => {
    const item = layout.focus.find((card) => card.item.id === id)?.item;
    const pinned = Boolean(pinState[id]);
    if (!item) return null;

    if (item.kind === 'dialogue') {
      return (
        <DialogueWidget
          messages={dialogueMessages.map((message) => ({
            id: message.id,
            role: message.role,
            text: message.text,
            createdAt: message.created_at,
            fields: message.fields,
            candidates: message.candidates
          }))}
          pinned={pinned}
          onTogglePin={() => actions.togglePin(item.id)}
          onSuggestionSelect={(candidate) => void actions.useClarificationCandidate(candidate)}
        />
      );
    }

    return (
      <div className="transition-all duration-300 ease-out">
        {item.kind === 'failure' ? <FailuresWidget items={[{ id: item.id, title: item.title, severity: item.severity ?? 'critical', ageMinutes: 0 }]} /> : null}
        {item.kind === 'approval' ? <ApprovalsWidget items={[{ id: item.id, title: item.title, detail: item.detail, requestedBy: 'Operator' }]} onApprove={(next) => void actions.approve(next)} onDeny={(next) => void actions.deny(next)} /> : null}
        {item.kind === 'reminder' ? <RemindersWidget items={[{ id: item.id, title: item.title, due: item.detail, urgency: 'high' }]} onDone={(next) => void actions.done(next)} /> : null}
        {item.kind === 'workflow' ? <WorkflowsWidget items={[{ id: item.id, title: item.title, progress: workflows.find((w) => w.id === item.id)?.progress ?? 0, stepLabel: item.detail, resumable: true }]} onResume={(next) => void actions.resume(next)} onPause={(next) => void actions.pause(next)} onAdvanceStep={(next) => void actions.advanceStep(next)} /> : null}
      </div>
    );
  };

  const onLogin = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    try {
      await login(username, password);
      setAuthReady(true);
      setStatusMessage('Logged in. Backend orchestration enabled.');
    } catch (error) {
      setStatusMessage(`Login failed: ${toErrorMessage(error)}`);
    } finally {
      setLoading(false);
    }
  };

  const onBootstrapInit = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    try {
      const response = await bootstrapInit(username, password);
      setBootstrapped(response.bootstrapped);
      setStatusMessage('Bootstrap initialized. Please log in.');
    } catch (error) {
      setStatusMessage(`Bootstrap init failed: ${toErrorMessage(error)}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-screen overflow-hidden bg-bg text-slate-200">
      <div className="px-4 pt-3 text-xs text-slate-400">{statusMessage || 'Checking backend status…'}</div>
      {pendingClarification ? (
        <div className="px-4 pt-1 text-[11px] text-amber-300/90">Clarification needed: respond with the missing details or pick a suggestion chip.</div>
      ) : null}
      <div className="grid h-full min-h-0 grid-cols-[64px_minmax(0,1fr)] gap-4 px-3 pb-28 pt-3">
        <LeftRail activeView={activeView} onChangeView={setActiveView} />
        <main className="h-full min-h-0 overflow-hidden pb-20">
          {activeView === 'overview' ? (
            <div className="grid h-full min-h-0 grid-cols-[minmax(0,1fr)_320px] gap-4">
              <section className="grid h-full min-h-0 grid-rows-[auto_minmax(0,1fr)] gap-3">
                {bootstrapped === false ? (
                  <form onSubmit={onBootstrapInit} className="flex flex-wrap items-center gap-2 rounded-lg border border-borderSoft/70 bg-panel p-3 text-xs">
                    <span className="text-slate-300">Initialize bootstrap:</span>
                    <input aria-label="Bootstrap username" value={username} onChange={(event) => setUsername(event.target.value)} className="rounded border border-borderSoft/70 bg-panelSoft/70 px-2 py-1 text-slate-100" />
                    <input aria-label="Bootstrap password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} className="rounded border border-borderSoft/70 bg-panelSoft/70 px-2 py-1 text-slate-100" />
                    <button disabled={loading} className="rounded border border-cyan-500/50 px-2 py-1 text-cyan-200">{loading ? 'Working…' : 'Init'}</button>
                  </form>
                ) : null}
                {bootstrapped && !authReady ? (
                  <form onSubmit={onLogin} className="flex flex-wrap items-center gap-2 rounded-lg border border-borderSoft/70 bg-panel p-3 text-xs">
                    <span className="text-slate-300">Login required:</span>
                    <input aria-label="Login username" value={username} onChange={(event) => setUsername(event.target.value)} className="rounded border border-borderSoft/70 bg-panelSoft/70 px-2 py-1 text-slate-100" />
                    <input aria-label="Login password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} className="rounded border border-borderSoft/70 bg-panelSoft/70 px-2 py-1 text-slate-100" />
                    <button disabled={loading} className="rounded border border-cyan-500/50 px-2 py-1 text-cyan-200">{loading ? 'Working…' : 'Login'}</button>
                    <button type="button" onClick={() => { setToken(null); setAuthReady(false); }} className="rounded border border-borderSoft/70 px-2 py-1 text-slate-300">Clear token</button>
                  </form>
                ) : null}

                <TimelineWidget
                  events={timelineEvents.map((event) => ({ ...event, bucket: 'Today' as const }))}
                  pinned={Boolean(pinState['timeline-stream'])}
                  onTogglePin={() => actions.togglePin('timeline-stream')}
                />
                <FocusLane placements={focusPlacements} renderWidget={renderFocusWidget} onReset={() => undefined} showReset={false} />
              </section>
              <ContextLane orderedIds={contextOrder} renderWidget={(kind) => <div className="transition-all duration-300 ease-out">{renderContextWidget(kind)}</div>} />
            </div>
          ) : null}
          {activeView === 'memories' ? <MemoriesScreen data={memoriesData} authenticated={authReady} error={viewErrors.memories} /> : null}
          {activeView === 'finance' ? <FinanceScreen data={financeData} authenticated={authReady} error={viewErrors.finance} /> : null}
          {activeView === 'files' ? <FilesScreen data={filesData} authenticated={authReady} error={viewErrors.files} /> : null}
          {activeView === 'camera' ? <CameraScreen data={cameraData} authenticated={authReady} error={viewErrors.camera} /> : null}
        </main>
      </div>

      <CommandDock
        alignToDialogue={true}
        onInteract={() => undefined}
        onTypingChange={() => undefined}
        onSubmit={(value) => {
          if (!authReady) {
            setStatusMessage('Please log in before issuing commands.');
            return;
          }
          void actions.sendCommand(value);
        }}
      />
      <BottomStatusStrip mode={'adaptive'} planner={'active'} executor={'ready'} domain={'automation'} confidence={'stable (78)'} onSimulate={() => undefined} />
    </div>
  );
}
