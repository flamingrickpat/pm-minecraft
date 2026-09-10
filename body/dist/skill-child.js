/**
 * Run generated TypeScript outside the body process.
 * API requests use pipes. Script errors return their names and messages.
 * EOF ends this process. The parent kills scripts that block the event loop.
 */
import { readSync, writeSync } from "node:fs";
import { createInterface } from "node:readline";
import { createContext, Script } from "node:vm";
import * as ts from "typescript";
const pending = new Map();
let nextId = 0;
let started = false;
function send(value) {
    writeSync(1, JSON.stringify(value) + "\n");
}
function responseValue(response) {
    if (response.error) {
        const error = new Error(response.error.message);
        error.name = response.error.name;
        throw error;
    }
    return response.value;
}
function call(method, args, sync) {
    const id = nextId++;
    if (!sync) {
        return new Promise((resolve, reject) => {
            pending.set(id, { resolve, reject });
            send({ kind: "call", id, method, args, sync });
        });
    }
    send({ kind: "call", id, method, args, sync });
    // A separate pipe preserves the two synchronous API methods.
    const bytes = [];
    const byte = Buffer.alloc(1);
    while (true) {
        if (readSync(3, byte, 0, 1, null) === 0)
            process.exit(0);
        if (byte[0] === 10)
            break;
        bytes.push(byte[0]);
    }
    return responseValue(JSON.parse(Buffer.from(bytes).toString("utf8")));
}
async function run(source, args, methods) {
    try {
        let javascript = ts.transpileModule(source, {
            compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022, esModuleInterop: true },
        }).outputText;
        javascript = javascript.replace(/export\s+default\s+/, "").replace(/export\s+/, "");
        javascript += "\n;this.__skillRun = run;";
        const api = new Proxy({}, {
            get(_target, property) {
                if (typeof property === "symbol")
                    return undefined;
                if (!methods.includes(property))
                    return () => {
                        const error = new Error(`The survival API does not expose '${property}'.`);
                        error.name = "AccessDenied";
                        throw error;
                    };
                return (value) => call(property, value, property === "findPath" || property === "findBlocks");
            },
        });
        const output = (stream) => (...values) => send({
            kind: "log", stream, text: values.map(stringify).join(" "),
        });
        const context = createContext({ api, console: {
                log: output("stdout"), info: output("stdout"), warn: output("stderr"), error: output("stderr"),
            } });
        new Script(javascript, { filename: "skill.ts" }).runInContext(context);
        const skill = context.__skillRun;
        if (typeof skill !== "function")
            throw new Error("The skill has no default run export.");
        await skill(api, args);
        send({ kind: "result", result: { status: "ok", reason: null } });
    }
    catch (error) {
        const value = error instanceof Object && "name" in error && "message" in error
            ? error : { name: "Error", message: String(error) };
        const status = value.name === "AccessDenied" ? "access_denied"
            : value.name === "SkillStopped" ? "stopped"
                : value.name === "SkillAbort" ? "timeout" : "typescript_error";
        send({ kind: "result", result: { status, reason: `${value.name}: ${value.message}` } });
    }
}
function stringify(value) {
    if (typeof value === "string")
        return value;
    try {
        return JSON.stringify(value);
    }
    catch {
        return String(value);
    }
}
const lines = createInterface({ input: process.stdin });
lines.on("line", (line) => {
    const message = JSON.parse(line);
    if (!started) {
        started = true;
        void run(message.source, message.args, message.methods);
        return;
    }
    const request = pending.get(message.id);
    pending.delete(message.id);
    try {
        request.resolve(responseValue(message));
    }
    catch (error) {
        request.reject(error);
    }
});
process.stdin.once("end", () => process.exit(0));
