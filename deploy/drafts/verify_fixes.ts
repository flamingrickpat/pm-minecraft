import { requireSuccessful, responseBlock, type SkillEntrypoint } from "../lib/minecraft";

/**
 * verify_fixes — post-restart verification for the 2026-08-17 fixes:
 *   1. Chest deposit/withdraw round-trip (windowType must be "chest")
 *   2. Viewport-independent mining (mine a block while NOT looking at it)
 *   3. attack_entity hits until the target is dead (no health fields)
 * Run this after the MCP/body server is restarted with the new build.
 */
const run: SkillEntrypoint = async (context) => {
  const results: Record<string, unknown> = {};

  // --- 1. Chest round-trip (deposit 3 seeds, withdraw 3 seeds) ---
  {
    const chestPos = { x: 144, y: 70, z: 20 }; // chest placed during the playtest
    const before = await context.observe();
    const seedsBefore = before.inventory.items.find((i) => i.name === "wheat_seeds")?.count ?? 0;
    if (seedsBefore < 3) throw new Error(`Chest test needs >=3 wheat_seeds, have ${seedsBefore}`);

    const opened = requireSuccessful(await context.useBlock(chestPos, true), "open chest");
    if (opened.data?.windowType !== "chest") {
      throw new Error(`Expected windowType "chest", got ${JSON.stringify(opened.data?.windowType)}`);
    }

    const deposited = requireSuccessful(await context.chestDeposit("wheat_seeds", 3), "deposit 3 seeds");
    const inChest = ((deposited.data?.windowContents as Array<{ name: string; count: number }> | undefined) ?? [])
      .find((s) => s.name === "wheat_seeds")?.count ?? 0;
    if (inChest !== 3) throw new Error(`Expected 3 wheat_seeds in chest, got ${inChest}`);

    const withdrawn = requireSuccessful(await context.chestWithdraw("wheat_seeds", 3), "withdraw 3 seeds");
    const remaining = ((withdrawn.data?.windowContents as Array<{ name: string; count: number }> | undefined) ?? [])
      .find((s) => s.name === "wheat_seeds")?.count ?? 0;
    if (remaining !== 0) throw new Error(`Expected 0 wheat_seeds left in chest, got ${remaining}`);

    const after = await context.observe();
    const seedsAfter = after.inventory.items.find((i) => i.name === "wheat_seeds")?.count ?? 0;
    if (seedsAfter !== seedsBefore) {
      throw new Error(`Seeds did not round-trip: ${seedsBefore} -> ${seedsAfter}`);
    }
    results.chest = `ok (3 wheat_seeds in and back out, windowType=chest, contents=${JSON.stringify(withdrawn.data?.windowContents)})`;
  }

  // --- 2. Viewport-independent mining ---
  {
    const found = requireSuccessful(await context.findBlock("stone", 12), "find visible stone");
    const pos = responseBlock(found);
    // Get within the 3-block tunnel allowance so the head-LOS gate is bypassed,
    // then deliberately look DOWN so the wall block is NOT in the view cone.
    await context.walkTo({ x: pos.x, y: pos.y, z: pos.z }, 2.5, 45).catch(() => undefined);
    requireSuccessful(await context.rotate(0, -80), "look away from the target");
    const mined = requireSuccessful(await context.mineBlock(pos, false, 30), "mine off-view block");
    if (mined.data?.resultBlockName !== "air") {
      throw new Error(`Expected resultBlockName "air", got ${JSON.stringify(mined.data?.resultBlockName)}`);
    }
    results.mining = "ok (mined a block that was not in the view cone; no 'Block not in view')";
  }

  // --- 3. Attack until dead ---
  {
    let mob: { id: number; name: string; kind: string; position: { x: number; y: number; z: number } } | null = null;
    const lookouts = [
      { x: 162, y: 70, z: 26 },
      { x: 150, y: 70, z: 28 },
      { x: 155, y: 70, z: 22 },
      { x: 146, y: 70, z: 19 }
    ];
    for (let i = 0; i < lookouts.length && !mob; i++) {
      await context.walkTo(lookouts[i], 1.5, 45).catch(() => undefined);
      await context.sleep(500);
      const obs = await context.observe();
      mob = (obs.nearbyEntities ?? []).find((e) => e.kind === "animal") as typeof mob;
    }
    if (!mob) throw new Error("No animal found for the attack test (world may be depopulated)");

    const res = requireSuccessful(await context.attackEntity(mob.id, true, 120, 5, 30), "attack until dead");
    const data = (res.data ?? {}) as Record<string, unknown>;
    if (data.killed !== true) throw new Error(`Expected killed:true, got ${JSON.stringify(data)}`);
    if ("healthBefore" in data || "healthAfter" in data) {
      throw new Error("healthBefore/healthAfter should have been removed from the response");
    }
    results.attack = `ok (${JSON.stringify(data)})`;
  }

  return results;
};

export default run;
