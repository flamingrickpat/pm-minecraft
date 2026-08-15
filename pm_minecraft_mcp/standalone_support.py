"""Small local file-writing and YAML helpers used by the MCP server."""

from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML


def atomic_write_bytes(path: Path, data: bytes) -> None:
    """Flush a temporary peer then atomically replace one file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, raw_temp = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(raw_temp)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        for attempt in range(4):
            try:
                os.replace(temporary, path)
                break
            except PermissionError:
                if attempt == 3:
                    raise
                time.sleep(0.01 * (2**attempt))
    finally:
        if temporary.exists():
            temporary.unlink()


def readable_yaml_bytes(value: Any) -> bytes:
    """Serialize plain data as readable UTF-8 YAML."""
    yaml = YAML(typ="safe")
    yaml.allow_unicode = True
    yaml.default_flow_style = False
    yaml.indent(mapping=2, sequence=4, offset=2)
    from io import StringIO

    stream = StringIO()
    yaml.dump(value, stream)
    return stream.getvalue().encode("utf-8")


def read_readable_yaml(path: Path) -> Any:
    """Read one YAML file with the safe loader."""
    yaml = YAML(typ="safe")
    return yaml.load(path.read_text(encoding="utf-8"))
