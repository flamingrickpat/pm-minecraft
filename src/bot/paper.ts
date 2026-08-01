import { createConnection } from "node:net";

/**
 * Paper reachability is external; probe the TCP endpoint and return a literal dependency status.
 *
 * @remarks
 * archetype: service-provider
 * owns: bounded TCP reachability checks for the configured Paper host and port.
 * not own: Mineflayer login, server startup, or fake readiness.
 * fails when: DNS lookup, connection, or timeout reports the server unreachable.
 * domain: `/api/health` uses this as dependency evidence before and during bot startup.
 * invariant: an unreachable Paper endpoint is reported as an external failure, not as success.
 */
export interface PaperReachability {
  reachable: boolean;
  checkedAt: string;
  error: string | null;
}

export async function checkPaperReachable(host: string, port: number, timeoutMs: number): Promise<PaperReachability> {
  const checkedAt = new Date().toISOString();

  return await new Promise<PaperReachability>((resolve) => {
    const socket = createConnection({ host, port });
    let settled = false;

    const finish = (result: PaperReachability): void => {
      if (settled) {
        return;
      }
      settled = true;
      socket.destroy();
      resolve(result);
    };

    socket.setTimeout(timeoutMs);
    socket.once("connect", () => finish({ reachable: true, checkedAt, error: null }));
    socket.once("timeout", () =>
      finish({
        reachable: false,
        checkedAt,
        error: `Paper server is not reachable at ${host}:${port}: connection timed out after ${timeoutMs}ms`
      })
    );
    socket.once("error", (error) =>
      finish({
        reachable: false,
        checkedAt,
        error: `Paper server is not reachable at ${host}:${port}: ${error.message}`
      })
    );
  });
}
