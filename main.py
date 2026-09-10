"""Start the Minecraft MCP from PyCharm or the command line."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import traceback


def main() -> int:
    parser = argparse.ArgumentParser(description="Start the Minecraft MCP.")
    parser.add_argument("env_file", nargs="?", type=Path, help="Path to the .env file.")
    arguments = parser.parse_args()
    try:
        from mcmcp.config import ENV_FILE, environment_template
        from mcmcp.server import main as start_server

        env_file = arguments.env_file or ENV_FILE
        if not env_file.is_file():
            print(f"The MCP configuration does not exist: {env_file}", file=sys.stderr)
            print("\nCreate it with this content:\n", file=sys.stderr)
            print(environment_template(), file=sys.stderr, end="")
            return -1
        start_server(env_file)
    except Exception:
        traceback.print_exc()
        return -1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
