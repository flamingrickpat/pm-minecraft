/**
 * Run one skill in a child process. The parent owns the deadline and PID.
 * Script errors return skill results. Process errors stop the current skill.
 * Shutdown sends EOF, then forces the child to exit after one second.
 */
import { spawn } from "node:child_process";
import { createInterface } from "node:readline";
import { fileURLToPath } from "node:url";
import { log } from "./log.js";
const EXIT_GRACE_MS = 1000;
class SkillRunner {
    pid = null;
    child = null;
    finish = null;
    constructor() {
        process.once("exit", () => {
            if (this.child !== null) {
                this.child.stdin.end();
                this.child.kill("SIGKILL");
            }
        });
        for (const signal of ["SIGINT", "SIGTERM"]) {
            process.once(signal, async () => {
                await this.close();
                process.exit(signal === "SIGINT" ? 130 : 143);
            });
        }
    }
    stop() {
        this.finish?.({ status: "stopped", reason: "The skill was stopped." });
    }
    async close() {
        if (this.child === null)
            return;
        const exited = new Promise((resolve) => this.child.once("close", () => resolve()));
        this.stop();
        await exited;
    }
    async run(source, args, budgetMs, api, cancel) {
        if (this.child !== null)
            throw new Error("A skill process is already active.");
        const started = performance.now();
        const child = spawn(process.execPath, [fileURLToPath(new URL("./skill-child.js", import.meta.url))], {
            stdio: ["pipe", "pipe", "pipe", "pipe"], windowsHide: true,
        });
        this.child = child;
        this.pid = child.pid ?? null;
        log("info", `skill process started pid=${this.pid}`);
        const stdout = [];
        const stderr = [];
        let heartbeats = 0;
        let result = null;
        let killTimer;
        let deadlineTimer;
        const lines = createInterface({ input: child.stdout });
        const outcome = new Promise((resolve) => {
            this.finish = (value) => {
                if (result !== null)
                    return;
                result = value;
                clearTimeout(deadlineTimer);
                child.stdin.end();
                log("info", `skill EOF sent pid=${this.pid} status=${value.status}`);
                killTimer = setTimeout(() => {
                    log("warning", `skill force kill pid=${child.pid}`);
                    child.kill("SIGKILL");
                }, EXIT_GRACE_MS);
                if (value.status !== "ok")
                    cancel();
            };
            deadlineTimer = setTimeout(() => this.finish({
                status: "timeout", reason: "The skill time budget expired.",
            }), budgetMs);
            child.on("error", (error) => this.finish({ status: "typescript_error", reason: error.message }));
            // A child can exit between a response and its pipe write.
            const pipeError = (error) => {
                if (error.code !== "EPIPE" && error.code !== "ERR_STREAM_DESTROYED")
                    throw error;
                if (result !== null)
                    return;
                this.finish({ status: "typescript_error", reason: "The skill pipe closed." });
            };
            child.stdin.on("error", pipeError);
            child.stdio[3].on("error", pipeError);
            child.stderr.on("data", (data) => stderr.push(String(data)));
            child.once("close", (code, signal) => {
                clearTimeout(deadlineTimer);
                clearTimeout(killTimer);
                lines.close();
                if (result === null) {
                    result = { status: "typescript_error", reason: `The skill process exited: code=${code}, signal=${signal}.` };
                    cancel();
                }
                log("info", `skill process exited pid=${child.pid} code=${code} signal=${signal}`);
                this.child = null;
                this.pid = null;
                this.finish = null;
                resolve({ ...result, stdout_tail: tail(stdout), stderr_tail: tail(stderr), heartbeats,
                    duration_ms: performance.now() - started });
            });
        });
        lines.on("line", async (line) => {
            const message = JSON.parse(line);
            if (result !== null)
                return;
            if (message.kind === "log") {
                (message.stream === "stdout" ? stdout : stderr).push(message.text);
            }
            else if (message.kind === "result") {
                this.finish(message.result);
            }
            else if (message.kind === "call") {
                let response;
                try {
                    const value = await api[message.method](message.args);
                    heartbeats += 1;
                    response = { id: message.id, value };
                }
                catch (error) {
                    const value = error;
                    response = { id: message.id, error: { name: value.name, message: value.message } };
                }
                if (result !== null)
                    return;
                const pipe = message.sync ? child.stdio[3] : child.stdin;
                pipe.write(JSON.stringify(response) + "\n");
            }
            else {
                throw new Error(`Unknown skill message: ${message.kind}`);
            }
        });
        child.stdin.write(JSON.stringify({ source, args, methods: Object.keys(api) }) + "\n");
        return outcome;
    }
}
function tail(lines) {
    return lines.length === 0 ? null : lines.slice(-20).join("\n");
}
export const skillRunner = new SkillRunner();
