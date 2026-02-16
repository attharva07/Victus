import type { VictusUIState } from '../types/victus-ui';
import type { VictusView } from '../components/LeftRail';

export type UIAction =
  | { type: 'hydrate'; payload: VictusUIState }
  | { type: 'set_loading'; payload: boolean }
  | { type: 'set_view'; payload: VictusView }
  | { type: 'set_typing'; payload: boolean }
  | { type: 'set_error'; payload?: string };
