# Operations

Local dev, checks, CI and deploy.

## Checks

| recipe | meaning |
|---|---|
| `just discourse` | Bring up the local stack (below); idempotent, rerun after a reboot. |
| `just lint` / `just fmt` | ruff check and format. |
| `just typecheck` | ty, warnings as errors. |
| `just test` | pytest; needs `just discourse` up. `just test -k playtest` runs one. |
| `just deploy` | Deploy to production (below): shows every change, then asks; `--dry` only shows. |
| `just secrets` | Edit the deploy's secrets (`deploy/secrets.sops.yaml`). |

Every check must pass before a landing.

## Local stack

`dev/discourse.sh` runs Discourse's own `discourse/discourse_dev` image (native arm64) as the
container `vekn-forum-discourse`, from a checkout at `.local/discourse`, as a
multisite of three sites — `fr.localhost`, `intl.localhost`, `playtest.localhost`, port 3000 —
plus the bridge's Postgres (`vekn-forum-discourse-db`, port 5434). Only the Rails server runs: no
Ember build, so HTML pages answer 503 while every redirect and JSON endpoint the bridge uses
works. It provisions each site for the bridge with `discourse/site.rb` — the settings of
[engine.md#login](engine.md#login) and the bridge's API key, the same script production runs — and
writes the bridge's environment to `.local/discourse.env`. The Discourse commit it checks out is
`discourse/ref`, production's too.
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
| `ARCHON_URL`, `ARCHON_API_URL` | archon's app and public API hosts; default to production (`archon.vekn.net`). |
| `ARCHON_CLIENT_ID`, `ARCHON_CLIENT_SECRET` | One archon client, registered with `profile:email` and `api:read`. |
| `DISCOURSE_SITES` | Space-separated site names, e.g. `fr intl playtest`. |
| `DISCOURSE_<SITE>_URL`, `_SECRET`, `_API_KEY` | The site's origin, DiscourseConnect secret, and a global admin API key. |
| `DISCOURSE_<SITE>_ADMINS` | Who is admin there: `ROLE` or `ROLE@COUNTRY`, comma-separated. |
| `DISCOURSE_<SITE>_MEMBERS` | Set only on a gated site: the roles it admits (`PT,PTC`). |

The web app is `bridge:app` (ASGI); the sweep is `vekn-bridge-sweep`.

## Deploy

**Production is `frankfurt`**, a [`server-setup`](https://github.com/lionel-panhaleux/server-setup)
box shared with archon beta, deployed by `just deploy` (pyinfra, `deploy/`) with the fleet's
`~/.ssh/deploy` key. `just setup frankfurt` in server-setup converges the host first. *(Decided
2026-09-26: iterate on an existing host rather than rent a dedicated one.)*

| name | serves |
|---|---|
| `forum.krcg.org` | the bridge |
| `intl.forum.krcg.org` | the international site: the launcher's default site, database `discourse`, `RAILS_DB=default` |
| `fr.forum.krcg.org` | the France site: database `discourse_fr`, `RAILS_DB=fr` |

A site is one entry in `SITES` in `deploy/deploy.py`. Its name must resolve to the host before a
deploy — the deploy refuses otherwise, since every failed Let's Encrypt validation counts against its
limit.

**Discourse** runs from its official launcher (`/var/discourse`, discourse_docker pinned in
`deploy.py`, Discourse at `discourse/ref`), one container `app` holding every site, its Postgres and
Redis. `containers/app.yml` is written by the deploy; a change to it runs `./launcher rebuild app`,
which takes every site down for minutes. The container publishes no port: its nginx listens on
`/var/discourse/shared/standalone/nginx.http.sock`, behind the host's nginx, which terminates TLS
(server-setup's `nginx_site`). It raises `DISCOURSE_MAX_ADMIN_API_REQS_PER_MINUTE` for the sweep,
sends mail through Gmail SMTP as `codex.of.the.damned@gmail.com`, and makes
`DISCOURSE_DEVELOPER_EMAILS` admin: the break-glass login at `/u/admin-login`. Each site's settings
come from `discourse/site.rb`, re-run whenever it or the site's values change.

**The bridge** runs as `vekn-forum-bridge` (uvicorn on `127.0.0.1:8030`, user `vekn_forum`, database
`vekn_forum` on the host cluster by peer auth), its environment in `/etc/vekn_forum/bridge.env`.
`vekn-forum-sweep.timer` runs the sweep hourly; the deploy runs it once more whenever a site is
provisioned, since it creates the role groups a login names.

**Backups.** The bridge's database is in the host's nightly Postgres backup. Each Discourse site
writes its own daily archive — database and uploads — under
`/var/discourse/shared/standalone/backups/<db>/`, and `vekn-forum-discourse-backup.timer` pushes
that directory to the fleet's restic bucket, repo `vekn_forum_discourse`. To restore one site:
`restic restore` the archive, drop it in that directory, then
`cd /var/discourse && ./launcher enter app` and `discourse enable_restore`, then `RAILS_DB=<db> discourse restore <file>`.

**Secrets** (`just secrets`): `bridge_secret`, `mail_password`, per site `<site>_connect_secret` and
`<site>_api_key` (the deploy gives both to the site and to the bridge), and
`archon_client_id`/`archon_client_secret`, added once registered — the one archon client of the Bridge table, registered on
archon production with `https://forum.krcg.org/callback`.
