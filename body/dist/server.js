/**
 * Expose the body only on its authenticated local HTTP boundary.
 *
 * Bad authorization returns 401. Unknown routes return 404. Malformed payloads
 * and body action bugs retain their exceptions and stop the process loudly.
 */
import { createServer } from "node:http";
import { log } from "./log.js";
export function startServer(body, host, port, token) {
    const server = createServer(async (request, response) => {
        const started = performance.now();
        try {
            await route(body, request, response);
        }
        catch (error) {
            const message = error instanceof Error ? error.message : String(error);
            log("error", `${request.method} ${request.url} failed: ${message}`);
            if (!response.headersSent) {
                writeJson(response, 500, {
                    error: {
                        type: error instanceof Error ? error.name : "Error",
                        message,
                    },
                });
            }
            else {
                response.end();
            }
        }
        log("info", `${request.method} ${request.url} ok in ${Math.round(performance.now() - started)} ms`);
        if (request.method === "POST") {
            log("debug", `snapshot after ${request.url}: ${body.debugSnapshot()}`);
        }
    });
    async function route(body, request, response) {
        if (request.headers.authorization !== `Bearer ${token}`) {
            writeJson(response, 401, { error: "access_denied" });
            return;
        }
        if (request.method === "GET" && request.url === "/state") {
            writeJson(response, 200, body.state());
            return;
        }
        if (request.method === "GET" && request.url === "/catalog") {
            writeJson(response, 200, body.catalog());
            return;
        }
        if (request.method === "POST" && request.url === "/blocks") {
            const value = await readJson(request);
            writeJson(response, 200, { blocks: body.blocks(value.positions) });
            return;
        }
        if (request.method === "POST" && request.url === "/observe") {
            const value = await readJson(request);
            const state = body.state();
            writeJson(response, 200, {
                ...state,
                nearby_blocks: body.nearbyBlocks(state.camera.feet_position, value.radius),
                nearby_entities: body.nearbyEntities(state.camera.feet_position, value.radius),
            });
            return;
        }
        if (request.method === "POST" && request.url === "/find_blocks") {
            const value = await readJson(request);
            writeJson(response, 200, body.findBlocks(value));
            return;
        }
        if (request.method === "GET" && request.url === "/raytrace") {
            writeJson(response, 200, body.raytrace());
            return;
        }
        if (request.method === "POST" && request.url === "/scan_horizon") {
            writeJson(response, 200, await body.scanHorizon());
            return;
        }
        if (request.method === "POST" && request.url === "/rotate") {
            const value = await readJson(request);
            writeJson(response, 200, { camera: await body.rotate(value.yaw_degrees, value.pitch_degrees, value.absolute) });
            return;
        }
        if (request.method === "POST" && request.url === "/look_at") {
            const value = await readJson(request);
            writeJson(response, 200, { camera: await body.lookAt(value.position) });
            return;
        }
        if (request.method === "POST" && request.url === "/fine_control") {
            const value = await readJson(request);
            writeJson(response, 200, await body.fineControl(value.controls, value.duration_ms));
            return;
        }
        if (request.method === "POST" && request.url === "/walk_visible") {
            const value = await readJson(request);
            writeJson(response, 200, await body.walkVisible(value.target, value.limit, value.timeout_ms));
            return;
        }
        if (request.method === "POST" && request.url === "/walk_exact") {
            const value = await readJson(request);
            writeJson(response, 200, await body.walkExact(value.target, value.timeout_ms));
            return;
        }
        if (request.method === "POST" && request.url === "/walk_surface") {
            const value = await readJson(request);
            writeJson(response, 200, await body.walkSurface(value.x, value.z, value.timeout_ms));
            return;
        }
        if (request.method === "POST" && request.url === "/find_path") {
            const value = await readJson(request);
            writeJson(response, 200, body.findPath(value.target, value.limit, value.timeout_ms));
            return;
        }
        if (request.method === "POST" && request.url === "/use_block") {
            const value = await readJson(request);
            writeJson(response, 200, await body.useBlock(value.position, value.kind));
            return;
        }
        if (request.method === "POST" && request.url === "/equip") {
            const value = await readJson(request);
            writeJson(response, 200, await body.equip(value.item));
            return;
        }
        if (request.method === "POST" && request.url === "/use_item") {
            writeJson(response, 200, await body.useItem());
            return;
        }
        if (request.method === "POST" && request.url === "/craft") {
            const value = await readJson(request);
            writeJson(response, 200, await body.craft(value.item, value.repetitions));
            return;
        }
        if (request.method === "POST" && request.url === "/mine") {
            const value = await readJson(request);
            writeJson(response, 200, await body.mine(value.position));
            return;
        }
        if (request.method === "POST" && request.url === "/attack") {
            const value = await readJson(request);
            writeJson(response, 200, await body.attack(value.entity_id, value.limit));
            return;
        }
        if (request.method === "POST" && request.url === "/chest_move") {
            const value = await readJson(request);
            writeJson(response, 200, await body.chestMove(value.position, value.item, value.count, value.direction));
            return;
        }
        if (request.method === "POST" && request.url === "/smelt") {
            const value = await readJson(request);
            writeJson(response, 200, await body.smelt(value.position, value.input, value.input_count, value.fuel, value.fuel_count));
            return;
        }
        if (request.method === "POST" && request.url === "/drop") {
            const value = await readJson(request);
            writeJson(response, 200, await body.dropItem(value.item, value.count));
            return;
        }
        if (request.method === "POST" && request.url === "/eat_best") {
            writeJson(response, 200, await body.eatBest());
            return;
        }
        if (request.method === "POST" && request.url === "/equip_best") {
            const value = await readJson(request);
            writeJson(response, 200, await body.equipBestTool(value.target));
            return;
        }
        if (request.method === "POST" && request.url === "/safe_dig") {
            const value = await readJson(request);
            writeJson(response, 200, await body.safeToDig(value.position));
            return;
        }
        if (request.method === "POST" && request.url === "/craft_max") {
            const value = await readJson(request);
            writeJson(response, 200, await body.craftMax(value.item, value.limit));
            return;
        }
        if (request.method === "POST" && request.url === "/sleep") {
            const value = await readJson(request);
            writeJson(response, 200, await body.sleep(value.bed ?? null));
            return;
        }
        if (request.method === "POST" && request.url === "/pillar_up") {
            writeJson(response, 200, await body.pillarUp());
            return;
        }
        if (request.method === "POST" && request.url === "/recipe_search") {
            const value = await readJson(request);
            writeJson(response, 200, await body.recipeSearch(value.item_names, value.craftable_now, value.limit));
            return;
        }
        if (request.method === "POST" && request.url === "/staircase_down") {
            const value = await readJson(request);
            writeJson(response, 200, await body.staircaseDown(value.depth, value.torch));
            return;
        }
        if (request.method === "POST" && request.url === "/execute_skill") {
            const value = await readJson(request);
            writeJson(response, 200, await body.executeSkill(value.path, value.source, value.arguments, value.budget_ms));
            return;
        }
        if (request.method === "POST" && request.url === "/stop") {
            const value = await readJson(request);
            writeJson(response, 200, await body.stopCommand(value.scope));
            return;
        }
        if (request.method === "GET" && request.url === "/screenshot") {
            writeJson(response, 200, await body.screenshot());
            return;
        }
        writeJson(response, 404, { error: "not_found" });
    }
    server.listen(port, host);
    return server;
}
async function readJson(request) {
    const chunks = [];
    for await (const chunk of request) {
        chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
    }
    return JSON.parse(Buffer.concat(chunks).toString("utf-8"));
}
function writeJson(response, status, value) {
    response.writeHead(status, { "content-type": "application/json; charset=utf-8" });
    response.end(JSON.stringify(value));
}
