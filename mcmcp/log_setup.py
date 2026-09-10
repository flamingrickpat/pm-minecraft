"""One plain-text log at ~/.pm/pm-minecraft/mcmcp.log.

MCMCP_LOG_LEVEL picks error, warning, info, or debug. The default is info.
Debug adds full tool payloads. The file is append-only and rotates at 10 MB.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path

LOG_DIRECTORY = Path(os.path.expanduser("~/.pm/pm-minecraft"))
LEVELS = ("error", "warning", "info", "debug")

_configured = False


def log_level() -> str:
    """Read the level from the environment and stop on unknown values."""
    value = os.environ.get("MCMCP_LOG_LEVEL", "info").lower()
    if value not in LEVELS:
        raise RuntimeError(f"MCMCP_LOG_LEVEL must be one of {', '.join(LEVELS)}: {value}")
    return value


def setup_logging() -> logging.Logger:
    """Create the shared mcmcp logger exactly once."""
    global _configured
    log_directory = LOG_DIRECTORY
    log_directory.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("mcmcp")
    if _configured:
        return logger
    handler = RotatingFileHandler(
        log_directory / "mcmcp.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(log_level().upper())
    logger.propagate = False
    _configured = True
    return logger
