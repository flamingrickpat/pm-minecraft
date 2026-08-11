"""Hatch build hook: copy Node runtime assets and example drafts into the package.

An installed wheel must be self-sufficient. This hook copies, at build time:

- ``src/``, ``public/``, ``patches/``, ``scripts/patch-prismarine-fullbright.mjs``,
  ``package.json``, ``package-lock.json``, and ``tsconfig.json`` into
  ``pm_minecraft_mcp/node/`` — the first-use bootstrap runs ``npm ci`` on these
  into a per-environment runtime directory.
- ``deploy/drafts/*.ts`` into ``pm_minecraft_mcp/drafts/`` — example skills that
  ``init_character`` deploys into new character workspaces.

Both target directories are build artifacts and gitignored.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class NodeAssetsBuildHook(BuildHookInterface):
    PLUGIN_NAME = "pm-minecraft-node-assets"

    def initialize(self, version: str, build_data: dict) -> None:
        root = Path(self.root)
        package = root / "pm_minecraft_mcp"

        node_dir = package / "node"
        if node_dir.exists():
            shutil.rmtree(node_dir)
        node_dir.mkdir()
        for name in ("package.json", "package-lock.json", "tsconfig.json"):
            source = root / name
            if not source.is_file():
                raise FileNotFoundError(f"Required Node manifest is missing: {source}")
            shutil.copy2(source, node_dir / name)
        for directory in ("src", "public", "patches"):
            source = root / directory
            if not source.is_dir():
                raise FileNotFoundError(f"Required Node asset directory is missing: {source}")
            shutil.copytree(source, node_dir / directory)
        scripts_dir = node_dir / "scripts"
        scripts_dir.mkdir()
        patch_script = root / "scripts" / "patch-prismarine-fullbright.mjs"
        if not patch_script.is_file():
            raise FileNotFoundError(f"Required patch script is missing: {patch_script}")
        shutil.copy2(patch_script, scripts_dir / patch_script.name)

        drafts_source = root / "deploy" / "drafts"
        drafts_target = package / "drafts"
        if drafts_target.exists():
            shutil.rmtree(drafts_target)
        drafts_target.mkdir()
        drafts = sorted(drafts_source.glob("*.ts")) if drafts_source.is_dir() else []
        if not drafts:
            raise FileNotFoundError(f"Example drafts are missing from {drafts_source}")
        for draft in drafts:
            shutil.copy2(draft, drafts_target / draft.name)
