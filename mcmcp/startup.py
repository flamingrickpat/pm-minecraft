"""Prepare one MCP installation before its server starts.

Configuration and repository incompatibilities are permanent failures: raise
immediately so the command prints the original error and exits.  This module
does not recover from a bad setup or silently replace character-owned files.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil

from .config import Configuration, PROJECT_ROOT


def initialize_agent_home(configuration: Configuration) -> None:
    """Create the standard writable character workspace without overwriting it."""
    home = configuration.agent_home
    home.mkdir(parents=True, exist_ok=True)
    for name in ("drafts", "skills", "memory", "frames"):
        (home / name).mkdir(exist_ok=True)

    draft_source = PROJECT_ROOT / "deploy" / "drafts"
    drafts = tuple(sorted(draft_source.glob("*.ts")))
    if not drafts:
        raise RuntimeError(f"Example drafts are missing: {draft_source}")
    for source in drafts:
        target = home / "drafts" / source.name
        if not target.exists():
            shutil.copyfile(source, target)

    instructions = home / "AGENTS.md"
    if not instructions.exists():
        template = (PROJECT_ROOT / "mcmcp" / "character_instructions.txt").read_text(encoding="utf-8")
        draft_list = "\n".join(f"  - drafts/{draft.name}" for draft in drafts)
        instructions.write_text(template.replace("@@DRAFT_LIST@@", draft_list).rstrip() + "\n", encoding="utf-8")


def patch_prismarine_viewer(body_root: Path) -> None:
    """Apply the small 1.19.4 compatibility patch after npm installs packages."""
    replacements = (
        ("node_modules/prismarine-viewer/viewer/lib/version.js", "'1.19', '1.20.1'", "'1.19', '1.19.4', '1.20.1'"),
        ("node_modules/prismarine-viewer/public/index.js", '"1.19","1.20.1"', '"1.19","1.19.4","1.20.1"'),
    )
    for relative, old, new in replacements:
        path = body_root / relative
        text = path.read_text(encoding="utf-8")
        if new in text:
            continue
        count = text.count(old)
        if count != 1:
            raise RuntimeError(f"{path}: expected one version-list target, found {count}")
        path.write_text(text.replace(old, new), encoding="utf-8")
        print(f"Prismarine viewer patched: {path}")

    for source, target in (
        ("node_modules/prismarine-viewer/public/textures/1.19.png", "node_modules/prismarine-viewer/public/textures/1.19.4.png"),
        ("node_modules/prismarine-viewer/public/blocksStates/1.19.json", "node_modules/prismarine-viewer/public/blocksStates/1.19.4.json"),
    ):
        source_path = body_root / source
        target_path = body_root / target
        if not target_path.is_file() or source_path.read_bytes() != target_path.read_bytes():
            shutil.copyfile(source_path, target_path)
            print(f"Prismarine viewer asset alias: {target_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply the local Prismarine Viewer compatibility patch.")
    parser.add_argument("--patch-prismarine", action="store_true")
    parser.add_argument("--body-root", type=Path, default=PROJECT_ROOT / "body")
    arguments = parser.parse_args()
    if not arguments.patch_prismarine:
        parser.error("--patch-prismarine is required")
    patch_prismarine_viewer(arguments.body_root)


if __name__ == "__main__":
    main()
