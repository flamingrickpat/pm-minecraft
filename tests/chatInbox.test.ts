import { describe, expect, it } from "vitest";
import { createChatInbox } from "../src/state/chatInbox.js";

describe("chat inbox", () => {
  it("retains a bounded ordered copy of non-empty server messages", () => {
    const inbox = createChatInbox(2);
    inbox.add(" first ", "chat");
    inbox.add("", "system");
    inbox.add("second", "system");
    inbox.add("third", "game_info");

    const messages = inbox.messages();
    expect(messages.map(({ text, position }) => ({ text, position }))).toEqual([
      { text: "second", position: "system" },
      { text: "third", position: "game_info" }
    ]);
    expect(new Set(messages.map((message) => message.id)).size).toBe(2);
    messages[0].text = "mutated";
    expect(inbox.messages()[0].text).toBe("second");
  });
});
