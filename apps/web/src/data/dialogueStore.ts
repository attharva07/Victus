export type DialogueMessage = { id: string; role: 'user' | 'system'; text: string; createdAt: number };

export const dialogueSeed: DialogueMessage[] = [
  { id: 'd1', role: 'system', text: 'Victus is active. Issue a command when ready.', createdAt: 0 }
];

export function appendDialogueExchange(messages: DialogueMessage[], text: string, now: number): DialogueMessage[] {
  const clean = text.trim();
  if (!clean) return messages;

  return [
    ...messages,
    { id: `d-user-${now}`, role: 'user', text: clean, createdAt: now },
    { id: `d-system-${now}`, role: 'system', text: `Acknowledged: ${clean}`, createdAt: now + 1 }
  ];
}
