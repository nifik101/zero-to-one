#!/usr/bin/env bash
set -euo pipefail

# Install uv (Python package and project manager) if it is not already present.
# The installer places binaries in $HOME/.local/bin and is safe to re-run.
if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi

export PATH="$HOME/.local/bin:$PATH"

# Create/refresh the project virtual environment from the lockfile.
# stdlib-only project: this is fast and fully idempotent.
uv sync
