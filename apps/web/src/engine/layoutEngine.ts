import { compositeScore, type AdaptiveItem } from './adaptiveScore';

export type LaneId = 'focus' | 'context' | 'timeline';
export type CardSizePreset = 'S' | 'M' | 'L' | 'XL' | 'FULL';
export type PinState = Record<string, { lane: Exclude<LaneId, 'timeline'>; order: number }>;

export type LayoutCard = {
  item: AdaptiveItem;
  lane: LaneId;
  size: CardSizePreset;
  score: number;
  pinned: boolean;
};

export type LayoutPlan = {
  focus: LayoutCard[];
  context: LayoutCard[];
  timeline: LayoutCard[];
};

const APPROVAL_FOCUS_THRESHOLD = 80;
const REMINDER_FOCUS_THRESHOLD = 78;
const WORKFLOW_FOCUS_THRESHOLD = 70;

function cardSizeForScore(score: number, kind: AdaptiveItem['kind']): CardSizePreset {
  if (kind === 'timeline') return 'FULL';
  if (score >= 92) return 'XL';
  if (score >= 80) return 'L';
  if (score >= 65) return 'M';
  return 'S';
}

function defaultLane(item: AdaptiveItem, score: number): LaneId {
  if (item.kind === 'timeline') return 'timeline';
  if (item.kind === 'failure') return 'focus';
  if (item.kind === 'alert' && item.severity === 'critical') return 'focus';
  if (item.kind === 'approval') return item.urgency > APPROVAL_FOCUS_THRESHOLD ? 'focus' : 'context';
  if (item.kind === 'reminder') return item.urgency > REMINDER_FOCUS_THRESHOLD ? 'focus' : 'context';
  if (item.kind === 'workflow') return score > WORKFLOW_FOCUS_THRESHOLD ? 'focus' : 'context';
  if (item.kind === 'dialogue') return 'focus';
  return 'context';
}

function sortCards(cards: LayoutCard[], pinState: PinState, lane: 'focus' | 'context') {
  const pinned = cards
    .filter((card) => card.pinned)
    .sort((a, b) => (pinState[a.item.id]?.order ?? 999) - (pinState[b.item.id]?.order ?? 999));
  const adaptive = cards.filter((card) => !card.pinned).sort((a, b) => b.score - a.score);
  return [...pinned, ...adaptive];
}

export function computeAdaptiveLayout(items: AdaptiveItem[], pinState: PinState = {}, now = Date.now()): LayoutPlan {
  const cards = items.map((item) => {
    const score = compositeScore(item, now);
    const pinnedMeta = pinState[item.id];
    const lane = pinnedMeta?.lane ?? defaultLane(item, score);
    return {
      item,
      lane,
      score,
      pinned: Boolean(pinnedMeta),
      size: cardSizeForScore(score, item.kind)
    } satisfies LayoutCard;
  });

  const timeline = cards
    .filter((card) => card.item.kind === 'timeline')
    .sort((a, b) => b.item.updatedAt - a.item.updatedAt)
    .map((card) => ({ ...card, lane: 'timeline' as const, size: 'FULL' as const }));

  const focusPool = cards.filter((card) => card.lane === 'focus' && card.item.kind !== 'timeline');
  const contextPool = cards.filter((card) => card.lane === 'context' && card.item.kind !== 'timeline');

  // Fill focus lane with next highest eligible cards to avoid visual gaps.
  const minFocusCards = 3;
  const sortedContext = [...contextPool].sort((a, b) => b.score - a.score);
  while (focusPool.length < minFocusCards && sortedContext.length > 0) {
    const next = sortedContext.shift();
    if (!next) break;
    if (next.item.kind === 'approval' && next.item.urgency <= APPROVAL_FOCUS_THRESHOLD) continue;
    const index = contextPool.findIndex((card) => card.item.id === next.item.id);
    if (index >= 0) contextPool.splice(index, 1);
    focusPool.push({ ...next, lane: 'focus' });
  }

  return {
    focus: sortCards(focusPool, pinState, 'focus'),
    context: sortCards(contextPool, pinState, 'context'),
    timeline
  };
}
