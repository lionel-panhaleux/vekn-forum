# Checks, local stack and deploy — wiki/operations.md.

# The local Discourse multisite and the bridge's Postgres; idempotent.
discourse:
    ./dev/discourse.sh

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
