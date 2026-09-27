# Checks, local stack and deploy — wiki/operations.md.

# The local Discourse multisite and the bridge's Postgres; idempotent.
discourse:
    ./dev/discourse.sh

# The bridge on localhost:8765, logging in through archon beta with the dev client in .local/archon.env.
bridge:
    #!/usr/bin/env bash
    set -euo pipefail
    if [ ! -f .local/archon.env ]; then
        echo "no .local/archon.env: register the dev archon client first (wiki/operations.md#local-stack)" >&2
        exit 1
    fi
    set -a
    source .local/discourse.env
    BRIDGE_URL=http://localhost:8765
    BRIDGE_SECRET=$(openssl rand -hex 16)
    ARCHON_URL=https://archon.krcg.org
    ARCHON_API_URL=https://api.archon.krcg.org
    source .local/archon.env
    set +a
    : "${ARCHON_CLIENT_ID:?missing from .local/archon.env}" "${ARCHON_CLIENT_SECRET:?missing from .local/archon.env}"
    exec uv run uvicorn bridge:app --port 8765 --reload --reload-dir src

lint:
    uv run ruff check
    uv run ruff format --check

fmt:
    uv run ruff check --fix
    uv run ruff format

typecheck:
    uv run --group deploy ty check --error-on-warning

# Needs `just discourse` up.
test *args:
    uv run pytest {{ args }}

# Deploy to frankfurt with pyinfra: shows every change, then asks (--dry only shows)
deploy *flags:
    cd deploy && uv run --group deploy pyinfra inventory.py deploy.py --diff {{ flags }}

# Edit the deploy's encrypted secrets in $EDITOR
secrets:
    cd deploy && sops edit secrets.sops.yaml
