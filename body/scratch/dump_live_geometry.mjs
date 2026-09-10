/** Dump the loaded production cave around big_chungus without changing it. */

import { writeFileSync } from "node:fs";
import mineflayer from "mineflayer";
import { Vec3 } from "vec3";

const bot = mineflayer.createBot({
  host: "127.0.0.1",
  port: 12345,
  username: "big_chungus",
  auth: "offline",
  version: "1.19.4",
  viewDistance: 16,
});

bot.once("spawn", () => {
  setTimeout(() => {
    const cells = [];
    for (let y = 55; y <= 125; y += 1) {
      for (let z = 10; z <= 110; z += 1) {
        for (let x = -20; x <= 15; x += 1) {
          cells.push({ x, y, z, name: bot.blockAt(new Vec3(x, y, z))?.name ?? "unloaded" });
        }
      }
    }
    writeFileSync(
      "C:/Temp/Chungus/live_cave_geometry.json",
      JSON.stringify({ position: bot.entity.position, cells }),
    );
    console.log(`wrote ${cells.length} cells`);
    bot.quit();
  }, 2000);
});

bot.on("error", error => { throw error; });
