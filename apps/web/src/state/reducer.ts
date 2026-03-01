import type { VictusView } from '../components/LeftRail';
import type { VictusUIState } from '../types/victus-ui';
import type { UIAction } from './actions';

export type StoreState = {
  data: VictusUIState | null;
  isLoading: boolean;
  isTyping: boolean;
  activeView: VictusView;
  error?: string;
  lastUpdatedAt?: number;
};

export const initialStoreState: StoreState = {
  data: null,
  isLoading: true,
  isTyping: false,
  activeView: 'overview'
};

export function storeReducer(state: StoreState, action: UIAction): StoreState {
  switch (action.type) {
    case 'hydrate':
      return { ...state, data: action.payload, isLoading: false, error: undefined, lastUpdatedAt: Date.now() };
    case 'set_loading':
      return { ...state, isLoading: action.payload };
    case 'set_typing':
      return { ...state, isTyping: action.payload };
    case 'set_view':
      return { ...state, activeView: action.payload };
    case 'set_error':
      return { ...state, error: action.payload, isLoading: false };
    default:
      return state;
  }
}
