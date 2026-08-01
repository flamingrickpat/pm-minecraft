import { randomUUID } from "node:crypto";

export interface MinecraftMessage {
  id: string;
  receivedAt: string;
  text: string;
  position: string;
}

export interface ChatInbox {
  add(text: string, position: string): void;
  messages(): MinecraftMessage[];
}

export function createChatInbox(limit = 100): ChatInbox {
  const sessionId = randomUUID();
  const entries: MinecraftMessage[] = [];
  let sequence = 0;

  return {
    add(text, position) {
      const normalized = text.trim();
      if (!normalized) return;
      entries.push({ id: `${sessionId}:${++sequence}`, receivedAt: new Date().toISOString(), text: normalized, position });
      if (entries.length > limit) entries.splice(0, entries.length - limit);
    },
    messages: () => entries.map((entry) => ({ ...entry }))
  };
}
