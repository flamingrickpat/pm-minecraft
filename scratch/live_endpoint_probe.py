"""Prove whether the configured game client and RCON command port share a server.

This only reads the live server. It never changes a world.
    uv run python scratch/live_endpoint_probe.py C:\\Temp\\Grog\\.env
"""

import sys

from mcrcon import MCRcon


def values(path):
    return {
        key: value
        for line in path.read_text(encoding="utf-8").splitlines()
        if line and not line.startswith("#")
        for key, value in [line.split("=", 1)]
    }


config = values(__import__("pathlib").Path(sys.argv[1]))
with MCRcon(
    config["MINECRAFT_RCON_HOST"],
    config["MINECRAFT_RCON_PASSWORD"],
    port=int(config["MINECRAFT_RCON_PORT"]),
) as rcon:
    print(f"game_endpoint={config['MINECRAFT_HOST']}:{config['MINECRAFT_PORT']}")
    print(f"rcon_endpoint={config['MINECRAFT_RCON_HOST']}:{config['MINECRAFT_RCON_PORT']}")
    print(f"rcon_list={rcon.command('list')}")
    print(
        "player_on_rcon_server="
        + rcon.command(
            f"execute as {config['MINECRAFT_PLAYER']} run data get entity @s Pos"
        )
    )
