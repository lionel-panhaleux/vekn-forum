# Checks, local stack and deploy — wiki/operations.md.

# The local stack until Ctrl-C, which stops it all: Discourse (fr, intl, playtest) with its Postgres,
# and the bridge on localhost:8765 through archon beta with the dev client in .local/archon.env.
dev:
    #!/usr/bin/env bash
    set -euo pipefail
    if [ ! -f .local/archon.env ]; then
        echo "no .local/archon.env: register the dev archon client first (wiki/operations.md#local-stack)" >&2
        exit 1
    fi
    trap 'just stop' EXIT
    ./dev/discourse.sh
    set -a
    source .local/discourse.env
    BRIDGE_URL=http://localhost:8765
    BRIDGE_SECRET=$(openssl rand -hex 16)
    ARCHON_URL=https://archon.krcg.org
    ARCHON_API_URL=https://api.archon.krcg.org
    source .local/archon.env
    set +a
    : "${ARCHON_CLIENT_ID:?missing from .local/archon.env}" "${ARCHON_CLIENT_SECRET:?missing from .local/archon.env}"
    uv run uvicorn bridge:app --port 8765 --reload --reload-dir src

# Stop whatever `just dev` started, from anywhere; stopping twice is harmless. The bridge is found by
# its port: a pattern would also match any shell whose command line names it.
stop:
    -@pids=$(lsof -ti tcp:8765 -sTCP:LISTEN) && kill $pids
    -@docker stop vekn-forum-discourse vekn-forum-discourse-db > /dev/null 2>&1

lint:
    uv run ruff check
    uv run ruff format --check

fmt:
    uv run ruff check --fix
    uv run ruff format

typecheck:
    uv run --group deploy ty check --error-on-warning

# vekn.fr's phpBB dump into the local fr site; needs `just dev` up.
import-phpbb dump:
    discourse/import/run.sh {{ dump }}

# Needs `just dev` up.
test *args:
    uv run pytest {{ args }}

# Deploy to frankfurt with pyinfra: shows every change, then asks (--dry only shows)
deploy *flags:
    cd deploy && uv run --group deploy pyinfra inventory.py deploy.py --diff {{ flags }}

# Edit the deploy's encrypted secrets in $EDITOR
secrets:
    cd deploy && sops edit secrets.sops.yaml
