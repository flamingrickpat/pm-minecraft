#!/usr/bin/env bash

set -euo pipefail

python_version="3.12"
refresh=false

usage() {
    printf 'Usage: %s [--python-version VERSION] [--refresh]\n' "${0##*/}"
}

while (($#)); do
    case "$1" in
        --python-version)
            (($# >= 2)) || { usage >&2; exit 2; }
            python_version="$2"
            shift 2
            ;;
        --refresh)
            refresh=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            printf 'Unknown option: %s\n' "$1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

for command in uv node npm; do
    if ! command -v "$command" >/dev/null 2>&1; then
        case "$command" in
            uv) printf 'uv is required. Install it from https://docs.astral.sh/uv/\n' >&2 ;;
            node) printf 'Node.js 20 or newer is required. Install it from https://nodejs.org/\n' >&2 ;;
            npm) printf 'npm was not found with Node.js. Reinstall Node.js, then rerun setup.\n' >&2 ;;
        esac
        exit 1
    fi
done

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
venv_path="$repo_root/.venv"
python_path="$venv_path/bin/python"
body_path="$repo_root/body"

if [[ ! -x "$python_path" ]]; then
    printf '==> Creating .venv with Python %s\n' "$python_version"
    uv venv --python "$python_version" "$venv_path"
else
    installed_version="$($python_path -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
    if [[ "$installed_version" != "$python_version" ]]; then
        actual_version="$($python_path --version 2>&1)"
        printf ".venv uses '%s', but this project requires Python %s. Remove .venv after checking it, then rerun.\n" "$actual_version" "$python_version" >&2
        exit 1
    fi
    printf '==> Reusing Python %s\n' "$installed_version"
fi

pushd "$repo_root" >/dev/null
if "$refresh"; then
    uv lock --upgrade
fi
uv sync --python "$python_path"
popd >/dev/null

pushd "$body_path" >/dev/null
npm ci || npm install
"$python_path" -m mcmcp.startup --patch-prismarine --body-root "$body_path"
npm run build
popd >/dev/null

"$python_path" -c "import fastmcp, pydantic, requests, ruamel.yaml; print('Python MCP environment ready')"
if [[ ! -f "$body_path/dist/main.js" ]]; then
    printf 'The body build output is missing: %s\n' "$body_path/dist/main.js" >&2
    exit 1
fi
node --version
printf 'Environment ready: %s\n' "$venv_path"
