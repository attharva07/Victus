import { createContext, useContext, useEffect, useMemo, useReducer } from 'react';
import { adaptProviderState } from '../adapters/uiStateAdapter';
import type { UIProvider } from '../providers/UIProvider';
import { mockProvider } from '../providers/mockProvider';
import type { ApprovalDecision, VictusUIState } from '../types/victus-ui';
import { initialStoreState, storeReducer, type StoreState } from './reducer';

type StoreActions = {
  decideApproval: (id: string, decision: ApprovalDecision) => Promise<void>;
  submitCommand: (text: string) => Promise<void>;
  ackAlert: (id: string) => Promise<void>;
  markReminderDone: (id: string) => Promise<void>;
  resumeWorkflow: (id: string) => Promise<void>;
  setActiveView: (view: StoreState['activeView']) => void;
  setTyping: (typing: boolean) => void;
};

const VictusStoreContext = createContext<{ state: StoreState; actions: StoreActions } | null>(null);

export function VictusStoreProvider({ children, provider = mockProvider }: { children: React.ReactNode; provider?: UIProvider }) {
  const [state, dispatch] = useReducer(storeReducer, initialStoreState);

  const hydrateFrom = async (task: () => Promise<VictusUIState>) => {
    dispatch({ type: 'set_loading', payload: true });
    try {
      const next = adaptProviderState(await task());
      dispatch({ type: 'hydrate', payload: next });
    } catch (error) {
      dispatch({ type: 'set_error', payload: error instanceof Error ? error.message : 'Provider operation failed' });
    }
  };

  useEffect(() => {
    void hydrateFrom(() => provider.getState());
  }, [provider]);

  const actions: StoreActions = useMemo(
    () => ({
      decideApproval: async (id, decision) => hydrateFrom(() => provider.decideApproval(id, decision)),
      submitCommand: async (text) => hydrateFrom(() => provider.submitCommand(text)),
      ackAlert: async (id) => hydrateFrom(() => provider.ackAlert(id)),
      markReminderDone: async (id) => hydrateFrom(() => provider.markReminderDone(id)),
      resumeWorkflow: async (id) => hydrateFrom(() => provider.resumeWorkflow(id)),
      setActiveView: (view) => dispatch({ type: 'set_view', payload: view }),
      setTyping: (typing) => dispatch({ type: 'set_typing', payload: typing })
    }),
    [provider]
  );

  return <VictusStoreContext.Provider value={{ state, actions }}>{children}</VictusStoreContext.Provider>;
}

export function useVictusStore() {
  const context = useContext(VictusStoreContext);
  if (!context) throw new Error('useVictusStore must be used inside VictusStoreProvider');
  return context;
}
