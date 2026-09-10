import process from "node:process";
import { MinecraftBody } from "./bot.js";
import { startServer } from "./server.js";

const body = new MinecraftBody({
  host: process.env.MINECRAFT_HOST!,
  port: Number(process.env.MINECRAFT_PORT!),
  version: process.env.MINECRAFT_VERSION!,
  username: process.env.MINECRAFT_PLAYER!,
  viewerPort: Number(process.env.MCMCP_VIEWER_PORT!),
  browserExecutable: process.env.BROWSER_EXECUTABLE_PATH!,
  walkReachedDistanceBlocks: Number(process.env.MCMCP_WALK_REACHED_DISTANCE_BLOCKS ?? "3"),
});
const server = startServer(
  body,
  process.env.MCMCP_BODY_HOST!,
  Number(process.env.MCMCP_BODY_PORT!),
  process.env.MCMCP_BODY_TOKEN!,
);
body.connect();

process.stdin.resume();
process.stdin.once("end", async () => {
  await body.close();
  server.close(() => process.exit(0));
});
