# Operations

Local dev, checks, CI and deploy.

## Checks

| recipe | meaning |
|---|---|
| `just discourse` | Bring up the local stack (below); idempotent, rerun after a reboot. |
| `just lint` / `just fmt` | ruff check and format. |
| `just typecheck` | ty, warnings as errors. |
| `just test` | pytest; needs `just discourse` up. `just test -k playtest` runs one. |

Every check must pass before a landing. Python 3.13 with uv, like the sibling VEKN services.

## Local stack

`dev/discourse.sh` runs Discourse's own `discourse/discourse_dev` image (native arm64) as the
container `vekn-forum-discourse`, from a checkout pinned in the script at `.local/discourse`, as a
multisite of three sites — `fr.localhost`, `intl.localhost`, `playtest.localhost`, port 3000 —
plus the bridge's Postgres (`vekn-forum-discourse-db`, port 5434). Only the Rails server runs: no
Ember build, so HTML pages answer 503 while every redirect and JSON endpoint the bridge uses
works. It provisions each site for the bridge (settings from [engine.md#login](engine.md#login),
the role groups, an API key) and writes the bridge's environment to `.local/discourse.env`.
`.local/` is gitignored; deleting it and both containers resets everything.

The tests serve the bridge on `localhost:8765` against those sites, and a stand-in archon on
`127.0.0.1:8766` that speaks archon's documented contract ([dogmas.md#testing](dogmas.md#testing)).

## Bridge

Configuration is read from the environment at point of use.

| variable | meaning |
|---|---|
| `BRIDGE_URL` | Its public origin; `<BRIDGE_URL>/callback` is the archon redirect URI. |
| `BRIDGE_SECRET` | Signs the login session cookie. |
| `DATABASE_URL` | Postgres holding the one table, `usernames`. |
| `ARCHON_URL`, `ARCHON_API_URL` | archon's app and public API hosts; default to beta. |
| `ARCHON_CLIENT_ID`, `ARCHON_CLIENT_SECRET` | One archon client, registered with `profile:email` and `api:read`. |
| `DISCOURSE_SITES` | Space-separated site names, e.g. `fr intl playtest`. |
| `DISCOURSE_<SITE>_URL`, `_SECRET`, `_API_KEY` | The site's origin, DiscourseConnect secret, and a global admin API key. |
| `DISCOURSE_<SITE>_ADMINS` | Who is admin there: `ROLE` or `ROLE@COUNTRY`, comma-separated. |
| `DISCOURSE_<SITE>_MEMBERS` | Set only on a gated site: the roles it admits (`PT,PTC`). |

The web app is `bridge:app` (ASGI); the sweep is `vekn-bridge-sweep`.

## Deploy

**Two deploy shapes.** Discourse runs from its official Docker launcher (multisite) on a dedicated
host — the one exception to the `server-setup` pattern, forced by the engine ([engine.md](engine.md)).
Its `app.yml` must set `DISCOURSE_MAX_ADMIN_API_REQS_PER_MINUTE` well above the default 60 for the
bridge's sweep. Everything we write (the login bridge) follows
[`server-setup`](https://github.com/lionel-panhaleux/server-setup): pyinfra, systemd, nginx, the shared
Postgres cluster.
