# Checks and local stack — wiki/operations.md.

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
    uv run ty check --error-on-warning

# Needs `just discourse` up.
test *args:
    uv run pytest {{ args }}
