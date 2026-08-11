"""First-use Node runtime bootstrap for installed wheels.

The wheel ships the Node sources (body, viewer assets, patches) and the
lockfile; the native Node dependency tree (mineflayer, better-sqlite3,
canvas, ...) is installed once per Python environment the first time the
body starts, and reused while the fingerprint of the manifests stays the
same. Source checkouts (and editable installs) simply use the repository
root, which ``setup.ps1`` already provisions with ``npm ci``.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

from filelock import FileLock

from . import __version__

_NODE_DIR_ENV = "PM_MINECRAFT_NODE_DIR"
_FINGERPRINT_NAME = "pm-minecraft-runtime.fingerprint"
_ASSET_FILES = ("package.json", "package-lock.json", "tsconfig.json")
_ASSET_DIRS = ("src", "public", "patches")
_POSTINSTALL_SCRIPT = "patch-prismarine-fullbright.mjs"


def package_root() -> Path:
    """Repository root in a source checkout, site-packages parent in a wheel."""
    return Path(__file__).resolve().parents[1]


def is_source_checkout() -> bool:
    """True when running from a repository checkout or editable install."""
    root = package_root()
    return (root / "package.json").is_file() and (root / "src" / "main.ts").is_file()


def node_executable() -> str:
    """Locate the Node.js executable or fail with an actionable message."""
    node = shutil.which("node.exe") or shutil.which("node")
    if node is None:
        raise RuntimeError(
            "Node.js was not found on PATH. Install Node.js 20 or newer "
            "(https://nodejs.org/), then retry."
        )
    return node


def npm_executable() -> str:
    """Locate the npm executable or fail with an actionable message."""
    npm = shutil.which("npm.cmd") or shutil.which("npm")
    if npm is None:
        raise RuntimeError(
            "npm was not found on PATH. Reinstall Node.js 20 or newer "
            "(https://nodejs.org/), then retry."
        )
    return npm


def runtime_dir() -> Path:
    """Directory holding the bootstrapped Node runtime for this environment."""
    override = os.environ.get(_NODE_DIR_ENV)
    if override:
        return Path(override).expanduser().resolve()
    return Path(sys.prefix) / "pm-minecraft-runtime" / __version__


def package_node_dir() -> Path:
    """Node manifests and body sources shipped inside the wheel."""
    return Path(__file__).resolve().parent / "node"


def _manifest_fingerprint() -> str:
    digest = hashlib.sha256()
    source = package_node_dir()
    for relative in (*_ASSET_FILES, *_ASSET_DIRS):
        path = source / relative
        if path.is_file():
            digest.update(relative.encode("utf-8"))
            digest.update(path.read_bytes())
        else:
            for child in sorted(path.rglob("*")):
                if child.is_file():
                    digest.update(child.relative_to(source).as_posix().encode("utf-8"))
                    digest.update(child.read_bytes())
    digest.update(__version__.encode("utf-8"))
    return digest.hexdigest()


def ensure_node_runtime() -> Path:
    """Return a ready-to-use Node runtime directory, bootstrapping it once.

    In a source checkout this is the repository root (provisioned by
    ``setup.ps1``). For installed wheels the first caller runs
    ``npm ci --omit=dev`` into a per-environment directory under a file
    lock; every later caller and process in the same environment reuses the
    finished directory until the manifests, patches, or package version
    change.
    """
    if is_source_checkout():
        root = package_root()
        tsx_cli = root / "node_modules" / "tsx" / "dist" / "cli.mjs"
        if not tsx_cli.is_file():
            raise RuntimeError(
                f"Node dependencies are missing in {root}. Run setup.ps1 "
                "(or npm ci) in the repository root first."
            )
        return root

    node_executable()
    npm_executable()
    target = runtime_dir()
    fingerprint = _manifest_fingerprint()
    fingerprint_path = target / _FINGERPRINT_NAME
    if fingerprint_path.is_file() and fingerprint_path.read_text(encoding="utf-8") == fingerprint:
        return target

    target.mkdir(parents=True, exist_ok=True)
    lock = FileLock(target.parent / f"{target.name}.lock")
    with lock:
        stored = fingerprint_path.read_text(encoding="utf-8") if fingerprint_path.is_file() else ""
        stored = stored or None
        if stored == fingerprint:
            return target
        _bootstrap(target, fingerprint)
    return target


def _bootstrap(target: Path, fingerprint: str) -> None:
    source = package_node_dir()
    if not (source / "package-lock.json").is_file():
        raise RuntimeError(f"Node manifests are missing from {source}")
    print(
        f"Installing the Node runtime into {target} (first use in this "
        "environment; this runs once and can take a few minutes)",
        file=sys.stderr,
        flush=True,
    )
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    for file_name in _ASSET_FILES:
        shutil.copy2(source / file_name, target / file_name)
    for dir_name in _ASSET_DIRS:
        shutil.copytree(source / dir_name, target / dir_name)
    scripts_dir = target / "scripts"
    scripts_dir.mkdir()
    shutil.copy2(source / "scripts" / _POSTINSTALL_SCRIPT, scripts_dir / _POSTINSTALL_SCRIPT)

    env = os.environ.copy()
    env["npm_config_fund"] = "false"
    env["npm_config_audit"] = "false"
    completed = subprocess.run(
        [npm_executable(), "ci", "--omit=dev"],
        cwd=target,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=1800,
    )
    if completed.returncode != 0:
        shutil.rmtree(target, ignore_errors=True)
        tail = "\n".join((completed.stdout + completed.stderr).splitlines()[-30:])
        raise RuntimeError(
            f"npm ci failed while bootstrapping the Node runtime in {target}:\n{tail}"
        )
    fingerprint_path = target / _FINGERPRINT_NAME
    fingerprint_path.write_text(fingerprint, encoding="utf-8")
    print(f"Node runtime ready: {target}", file=sys.stderr, flush=True)
