/**
 * This process owns the setup player and the operator.
 *
 * Code errors stop the process.
 * Minecraft connection errors stop the process and preserve the error.
 * The setup player leaves before the MCP connects with the same name.
 * Each input line produces one JSON response line.
 */

import readline from "node:readline";
import { appendFileSync, mkdirSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import mineflayer from "mineflayer";
import { Vec3 } from "vec3";

const [host, portText, version, playerName, operatorName] = process.argv.slice(2);
const port = Number(portText);
const logDirectory = join(homedir(), ".pm", "pm-minecraft");
mkdirSync(logDirectory, { recursive: true });
const logFilePath = join(logDirectory, "driver.log");

function log(level, message) {
  const line = `${new Date().toISOString()} ${level.toUpperCase()} ${message}`;
  try {
    appendFileSync(logFilePath, line + "\n");
  } catch {
    // Never let logging break the request it describes.
  }
  if (level === "error" || level === "warning") {
    console.error(line);
  }
}

const observedEvents = {
  blockBreaks: [],
  hurtEntities: [],
  chestLids: []
};

function createBot(username) {
  const bot = mineflayer.createBot({
    host,
    port,
    username,
    auth: "offline",
    version,
    viewDistance: 12
  });
  bot.on("kicked", reason => log("error", `${username} kicked: ${JSON.stringify(reason)}`));
  bot.on("end", reason => log("error", `${username} disconnected: ${reason}`));
  bot.on("death", () => log("warning", `${username} died`));
  return bot;
}

function waitForSpawn(bot) {
  return new Promise((resolve, reject) => {
    bot.once("spawn", resolve);
    bot.once("error", reject);
    bot.once("kicked", reason => reject(new Error(`${bot.username} was kicked: ${JSON.stringify(reason)}`)));
    bot.once("end", reason => reject(new Error(`${bot.username} disconnected before spawn: ${reason}`)));
  });
}

function state(bot) {
  return {
    username: bot.username,
    gameMode: bot.game.gameMode,
    difficulty: bot.game.difficulty,
    dimension: bot.game.dimension,
    health: bot.health,
    food: bot.food,
    oxygen: bot.oxygenLevel,
    experience: bot.experience,
    isRaining: bot.isRaining,
    timeOfDay: bot.time.timeOfDay,
    heldItem: bot.heldItem?.name ?? null,
    onGround: bot.entity.onGround,
    yaw: bot.entity.yaw,
    pitch: bot.entity.pitch,
    position: {
      x: bot.entity.position.x,
      y: bot.entity.position.y,
      z: bot.entity.position.z
    }
  };
}

function inventory(bot) {
  return bot.inventory.slots.map((item, slot) => item === null ? {
    slot,
    name: null,
    count: 0
  } : {
    name: item.name,
    displayName: item.displayName,
    count: item.count,
    slot,
    type: item.type,
    metadata: item.metadata,
    durabilityUsed: item.durabilityUsed,
    nbt: item.nbt ?? null
  });
}

function entities(bot) {
  return Object.values(bot.entities).map(entity => ({
    id: entity.id,
    uuid: entity.uuid ?? null,
    name: entity.name ?? null,
    type: entity.type,
    username: entity.username ?? null,
    yaw: entity.yaw,
    pitch: entity.pitch,
    metadata: entity.metadata,
    item: entity.name === "item" && entity.getDroppedItem !== undefined ? {
      name: entity.getDroppedItem().name,
      count: entity.getDroppedItem().count
    } : null,
    position: {
      x: entity.position.x,
      y: entity.position.y,
      z: entity.position.z
    }
  }));
}

function players() {
  return Object.entries(operator.players).map(([username, value]) => ({
    username,
    entityId: value.entity?.id ?? null,
    heldItem: value.entity?.heldItem?.name ?? null,
    yawDegrees: value.entity == null ? null : ((value.entity.yaw * 180 / Math.PI) % 360 + 360) % 360,
    pitchDegrees: value.entity == null ? null : value.entity.pitch * 180 / Math.PI,
    position: value.entity == null ? null : {
      x: value.entity.position.x,
      y: value.entity.position.y,
      z: value.entity.position.z
    }
  }));
}

function blockCounts(start, end) {
  const counts = {};
  for (let x = Math.min(start.x, end.x); x <= Math.max(start.x, end.x); x += 1) {
    for (let y = Math.min(start.y, end.y); y <= Math.max(start.y, end.y); y += 1) {
      for (let z = Math.min(start.z, end.z); z <= Math.max(start.z, end.z); z += 1) {
        const name = operator.blockAt(new Vec3(x, y, z))?.name ?? null;
        counts[name] = (counts[name] ?? 0) + 1;
      }
    }
  }
  return counts;
}

async function operatorCommand(text) {
  // Wait until the reply stream goes quiet instead of a fixed 500 ms.
  // Large /fill and /clear replies arrive after a slow server tick; a fixed
  // delay could return before the command completed. 400 ms of silence after
  // the last message means the server stopped talking.
  const messages = [];
  const record = message => messages.push(message);
  operator.on("messagestr", record);
  const line = text.startsWith("/") ? text : `/${text}`;
  // The server kicks a client that sends a chat or command string over the
  // 256-character protocol limit, which would poison the whole session.
  if (line.length > 256) {
    throw new Error(`Command is ${line.length} characters; the protocol limit is 256: ${text}`);
  }
  log("info", `> ${text}`);
  operator.chat(line);
  const startedAt = Date.now();
  const quietMs = 400;
  const capMs = 15000;
  let previousCount = 0;
  let quietSince = startedAt;
  while (Date.now() < startedAt + capMs) {
    await new Promise(resolve => setTimeout(resolve, 60));
    if (messages.length !== previousCount) {
      previousCount = messages.length;
      quietSince = Date.now();
    } else if (Date.now() - quietSince >= quietMs) {
      break;
    }
  }
  operator.removeListener("messagestr", record);
  if (messages.length === 0) {
    log("warning", `< no reply to ${text} after ${Date.now() - startedAt} ms; the command may not have executed`);
  } else {
    log("info", `< [${messages.join(" | ")}]`);
  }
  return messages;
}

async function releasePlayer() {
  const ended = new Promise(resolve => player.once("end", resolve));
  player.quit("The MCP now owns this player name.");
  await ended;
  player = null;
  return { released: playerName };
}

function waitForVitals(expected, label) {
  if (expected()) {
    return Promise.resolve();
  }
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      player.removeListener("health", changed);
      reject(new Error(`${label} did not reach the requested value.`));
    }, 20000);
    const changed = () => {
      if (expected()) {
        clearTimeout(timeout);
        player.removeListener("health", changed);
        resolve();
      }
    };
    player.on("health", changed);
  });
}

async function setVitals(health, food) {
  if (food < player.food) {
    const waiting = waitForVitals(() => player.food <= food, "Player food");
    operator.chat(`/effect give ${playerName} minecraft:hunger 30 255 true`);
    await waiting;
    await operatorCommand(`effect clear ${playerName} minecraft:hunger`);
  } else if (food > player.food) {
    const waiting = waitForVitals(() => player.food >= food, "Player food");
    operator.chat(`/effect give ${playerName} minecraft:saturation 30 0 true`);
    await waiting;
    await operatorCommand(`effect clear ${playerName} minecraft:saturation`);
  }
  if (player.food !== food) {
    throw new Error(`Player food is ${player.food}, not ${food}.`);
  }

  if (health < player.health) {
    const waiting = waitForVitals(() => player.health <= health, "Player health");
    operator.chat(`/damage ${playerName} ${player.health - health} minecraft:generic`);
    await waiting;
  } else if (health > player.health) {
    const waiting = waitForVitals(() => player.health >= health, "Player health");
    operator.chat(`/effect give ${playerName} minecraft:instant_health 1 31 true`);
    await waiting;
    await operatorCommand(`effect clear ${playerName} minecraft:instant_health`);
  }
  if (Math.abs(player.health - health) > 0.01) {
    throw new Error(`Player health is ${player.health}, not ${health}.`);
  }
  return { health: player.health, food: player.food };
}

async function digBlock(position) {
  // The setup player digs one complete block so the operator observes
  // blockBreakProgressObserved events for the during-action waits.
  const block = player.blockAt(new Vec3(position.x, position.y, position.z));
  if (block === null || ["air", "cave_air", "void_air"].includes(block.name)) {
    throw new Error(`Cannot dig ${block?.name ?? "nothing"} at the requested position.`);
  }
  await player.dig(block, true);
  return { dug: block.name, position };
}

async function attackEntity(options) {
  // The setup player hits one tagged entity so the operator observes the
  // entityHurt animation, exactly like the MCP player does in the real
  // entity_hurt during-action scenario. Command damage does not broadcast
  // the hurt animation to clients.
  const target = player.entities[options.entityId];
  if (target === undefined) {
    throw new Error(`No entity with id ${options.entityId}.`);
  }
  const observed = new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      operator.removeListener("entityHurt", hurt);
      reject(new Error(`The operator did not observe damage to entity ${target.id}.`));
    }, 5000);
    const hurt = entity => {
      if (entity.id === target.id) {
        clearTimeout(timeout);
        operator.removeListener("entityHurt", hurt);
        resolve();
      }
    };
    operator.on("entityHurt", hurt);
  });
  await player.attack(target, true);
  await observed;
  return { attacked: target.name, id: target.id };
}

async function container(position) {
  const block = operator.blockAt(new Vec3(position.x, position.y, position.z));
  const window = await operator.openContainer(block);
  const slots = window.slots.slice(0, window.inventoryStart).map((item, slot) => item === null ? {
    slot,
    name: null,
    count: 0
  } : {
    slot,
    name: item.name,
    count: item.count,
    nbt: item.nbt ?? null
  });
  window.close();
  return { title: window.title, type: window.type, slots };
}

async function handle(request) {
  if (request.action === "state") {
    return state(request.bot === "operator" ? operator : player);
  }
  if (request.action === "command") {
    return { messages: await operatorCommand(request.command) };
  }
  if (request.action === "inventory") {
    return inventory(request.bot === "operator" ? operator : player);
  }
  if (request.action === "entities") {
    return entities(request.bot === "player" ? player : operator);
  }
  if (request.action === "players") {
    return players();
  }
  if (request.action === "block") {
    const bot = request.bot === "player" ? player : operator;
    const block = bot.blockAt(new Vec3(request.x, request.y, request.z));
    return {
      name: block?.name ?? null,
      stateId: block?.stateId ?? null,
      properties: block?.getProperties() ?? null,
      boundingBox: block?.boundingBox ?? null,
      position: { x: request.x, y: request.y, z: request.z }
    };
  }
  if (request.action === "block_counts") {
    return blockCounts(request.start, request.end);
  }
  if (request.action === "dig_block") {
    return await digBlock(request.position);
  }
  if (request.action === "attack_entity") {
    return await attackEntity(request);
  }
  if (request.action === "container") {
    return await container(request.position);
  }
  if (request.action === "observed_events") {
    return observedEvents;
  }
  if (request.action === "release_player") {
    return await releasePlayer();
  }
  if (request.action === "set_vitals") {
    return await setVitals(request.health, request.food);
  }
  if (request.action === "shutdown") {
    if (player !== null) {
      player.quit("Test teardown");
    }
    operator.quit("Test teardown");
    return { stopped: true };
  }
  throw new Error(`Unknown driver action: ${request.action}`);
}

let player = createBot(playerName);
await waitForSpawn(player);
const operator = createBot(operatorName);
await waitForSpawn(operator);

operator.on("blockBreakProgressObserved", (block, destroyStage, entity) => {
  observedEvents.blockBreaks.push({
    position: { x: block.position.x, y: block.position.y, z: block.position.z },
    destroyStage,
    entityId: entity?.id ?? null
  });
});
operator.on("entityHurt", entity => {
  observedEvents.hurtEntities.push(entity.id);
});
operator.on("chestLidMove", (block, isOpen) => {
  observedEvents.chestLids.push({
    position: { x: block.position.x, y: block.position.y, z: block.position.z },
    isOpen
  });
});

process.stdout.write(`${JSON.stringify({ event: "ready", player: state(player), operator: state(operator) })}\n`);

const lines = readline.createInterface({ input: process.stdin });
for await (const line of lines) {
  const request = JSON.parse(line);
  const result = await handle(request);
  process.stdout.write(`${JSON.stringify({ id: request.id, result })}\n`);
  if (request.action === "shutdown") {
    process.exit(0);
  }
}
