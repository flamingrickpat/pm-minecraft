"""Start the persistent Minecraft server for live tests.

Invalid configuration values and an occupied Minecraft port stop this script.
Minecraft startup errors remain visible in the console and stop this script.
Ctrl+C reverts the world, removes non-player entities, and stops the server.
"""

from __future__ import annotations

import os
import subprocess
import threading
import time

from test_infrastructure.live_test import load_configuration, port_listening


SETUP_COMMANDS = (
    "gamerule doMobSpawning false",
    "gamerule doTraderSpawning false",
    "gamerule doPatrolSpawning false",
    "gamerule doInsomnia false",
    "gamerule playersSleepingPercentage 0",
    "gamerule keepInventory false",
    "gamerule spawnRadius 0",
    "gamerule spawnRadius 0",
    "setworldspawn 0 1 0",
    # The last session may have left blocks above the floor (a placed bed is
    # the known case). Commit only a clean flat area or every later revert
    # restores that leftover and the flat-area fill drops it as an item.
    # 81x4x81 bands stay under the 32768-cell fill limit.
    "fill -40 1 -40 40 4 40 air",
    "fill -40 5 -40 40 8 40 air",
    "fill -40 9 -40 40 12 40 air",
    "fill -40 13 -40 40 16 40 air",
    "kill @e[type=!minecraft:player]",
    "kill @e[type=!minecraft:player]",
    "commit",
)


def send_commands(
    process: subprocess.Popen[str],
    commands: tuple[str, ...],
    input_lock: threading.Lock,
) -> None:
    with input_lock:
        for command in commands:
            process.stdin.write(command + "\n")
        process.stdin.flush()


def stream_output(
    process: subprocess.Popen[str],
    checkpoint_created: threading.Event,
    input_lock: threading.Lock,
) -> None:
    setup_sent = False
    for line in process.stdout:
        print(line, end="")
        if "Done (" in line and not setup_sent:
            send_commands(process, SETUP_COMMANDS, input_lock)
            setup_sent = True
        if "Committed world baseline" in line:
            checkpoint_created.set()
            print("Checkpoint server ready. Press Ctrl+C to stop.")

def main() -> int:
    configuration = load_configuration()
    if not configuration.use_server_checkpointing:
        raise SystemExit("Set USE_SERVER_CHECKPOINTING=true in .env before you start this server.")
    if port_listening(configuration.minecraft_host, configuration.minecraft_port):
        raise SystemExit(
            f"Port {configuration.minecraft_port} is already in use. Stop its process and start this server again."
        )

    creation_flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) if os.name == "nt" else 0
    process = subprocess.Popen(
        [
            str(configuration.java),
            f"-Xms{configuration.server_memory}",
            f"-Xmx{configuration.server_memory}",
            "-jar",
            str(configuration.server_jar),
            "--port",
            str(configuration.minecraft_port),
            "nogui",
        ],
        cwd=configuration.server_template,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        errors="replace",
        creationflags=creation_flags,
        start_new_session=os.name != "nt",
    )

    checkpoint_created = threading.Event()
    input_lock = threading.Lock()
    output_thread = threading.Thread(
        target=stream_output,
        args=(process, checkpoint_created, input_lock),
    )
    output_thread.start()
    try:
        while process.poll() is None:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nStopping the checkpoint server...")
        if process.poll() is None:
            cleanup = (
                (
                    "revert",
                    "kill @e[type=!minecraft:player]",
                    "kill @e[type=!minecraft:player]",
                    "save-all flush",
                    "stop",
                )
                if checkpoint_created.is_set()
                else ("stop",)
            )
            send_commands(process, cleanup, input_lock)
            process.wait()

    exit_code = process.wait()
    output_thread.join()
    if not checkpoint_created.is_set() and exit_code == 0:
        raise SystemExit("Minecraft stopped before it created the checkpoint.")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
