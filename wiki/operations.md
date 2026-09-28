# Operations

Local dev, checks, CI and deploy.

## Checks

| recipe | meaning |
|---|---|
| `just dev` | The local stack (below) until Ctrl-C, which stops all of it; rerun after changing the theme or a site's tokens. |
| `just stop` | Stop what `just dev` started, from anywhere: an agent runs it before finishing. |
| `just lint` / `just fmt` | ruff check and format. |
| `just typecheck` | ty, warnings as errors. |
| `just test` | pytest; needs `just dev` up. `just test -k playtest` runs one. |
| `just import-phpbb <dump.sql>` | vekn.fr's phpBB into the local fr site (below). |
| `just deploy` | Deploy to production (below): shows every change, then asks; `--dry` only shows. |
| `just secrets` | Edit the deploy's secrets (`deploy/secrets.sops.yaml`). |

Every check must pass before a landing.

## Local stack

`dev/discourse.sh` runs Discourse's own `discourse/discourse_dev` image (native arm64) as the
container `vekn-forum-discourse`, from a checkout at `.local/discourse`, as a
multisite of three sites — `fr.localhost`, `intl.localhost`, `playtest.localhost`, port 3000 —
plus the bridge's Postgres (`vekn-forum-discourse-db`, port 5434). Rails runs in production mode:
we never change Discourse's code, and development mode's reloading made every page cost half a
second. The web server alone runs, serving its own assets — no nginx, no Sidekiq. The assets are
built once per Discourse commit (Discourse downloads them prebuilt for a release; log:
`.local/assets.log`), and per-IP limits are off, since the bridge and the tests reach every site
from one address. It provisions each
site with `discourse/site.rb` — the settings of [engine.md#login](engine.md#login), the base theme
from `theme/`, the site's tokens from `discourse/sites/<site>/` when it has some, and the bridge's
API key, the same script production runs — and writes the bridge's environment to
`.local/discourse.env`, keeping each site's secret and API key across runs so a running bridge
survives a re-provisioning. The Discourse commit it checks out is `discourse/ref`, production's too.
`.local/` is gitignored; deleting it and both containers resets everything.

`just dev` runs it, then serves the bridge on `localhost:8765`, where every local site's login button
points, logging in through archon beta (`archon.krcg.org`) as yourself. It reads the local sites from
`.local/discourse.env` and a dev archon client from `.local/archon.env` (`ARCHON_CLIENT_ID=…`,
`ARCHON_CLIENT_SECRET=…`): registered on beta from Developer like production's, with `profile:email`
and `api:read`, but its own client, with `http://localhost:8765/callback` as redirect URI. Leaving
it — Ctrl-C, or `just stop` from elsewhere — stops the bridge and both containers, so each `just dev`
starts cold: about half a minute, and a few minutes more the first time on a new Discourse commit.

The tests serve their own bridge on `localhost:8767`, with its own database (`bridge_test`), and a
stand-in archon on `127.0.0.1:8766` that speaks archon's documented contract
([dogmas.md#testing](dogmas.md#testing)), so `just dev` can stay up through a run. They share the
sites: for the run, each site's login button points at the test bridge, and is pointed back after —
a killed run leaves it there until the next run or `just dev`. Without a dev archon client, the
tests need only `dev/discourse.sh`, which brings up the sites without the bridge; `just stop` stops
them too. The role groups are created at the
start of a run, as the first sweep after a deploy does.

## phpBB import

`just import-phpbb <dump.sql>` imports vekn.fr's phpBB 3.3 into the local fr site
(`discourse/import/run.sh`; `run.sh <dump> app /var/www/discourse` on a launcher host). It loads the
dump's `phpbb3_` tables into a MariaDB (container `vekn-phpbb`, network `vekn-import`) created for
the run and removed after it, since it holds every member's email, then
runs in the Discourse container, on the fr database: `prepare.rb`, Discourse's own
`script/import_scripts/phpbb3.rb` with `phpbb-fr.yml`, then `finish.rb`. Every imported record keeps
its phpBB id (`import_id`), so a re-run with a fresher dump adds only what is new. The bundle is
Discourse's plus `mysql2` (`discourse/import/Gemfile`). About 1,700 posts a minute, an hour and a
half for vekn.fr.

What the forum becomes:

- **Boards.** Each public board goes into the site's section of its kind (`vekn.sections`) or is
  merged into one (`category_mappings`); the six regional boards and the four archived ones become
  subcategories of Domaines de France and Archives, with their icon. The private boards become
  restricted subcategories (`vekn.restricted`), staff-only from before any topic lands so they are
  never public, then opened to the groups phpBB granted them, `trust_level_0` for its registered
  members — archon's role group in place of phpBB's copy of a role, so `prince` and `judge` admit
  every holder of that role, not phpBB's French list. A board is merged into a restricted one only
  if it was readable by at least everyone who reads that one. Playtest Ind's NDA content is read by
  PT and PTC holders and the site's staff ([engine.md#model-mapping](engine.md#model-mapping)). The
  role groups must exist before the import, as the first sweep after a deploy leaves them.
- **Groups.** phpBB's groups are kept under the names `vekn.groups` gives them, members and owners
  included, each visible to its members and staff: they are the coordinator's
  ([engine.md#model-mapping](engine.md#model-mapping)). Those copying an archon role (Judges, Prince,
  Playtest) are not.
- **Members.** Every phpBB account, with its email: the legacy claim of
  [engine.md#login](engine.md#login). A member who logged in before the import is given their phpBB
  account's posts. Until claimed, an account keeps no phpBB admin or moderator right and is
  inactive, so Discourse mails it nothing: a reply to a years-old topic would otherwise mail its
  author's old address. The claim's login activates it. The site's
  `purge_unactivated_users_grace_period_days` stays 0: any other value deletes the post-less ones,
  group members among them. A guest's posts go to a suspended
  placeholder. Two phpBB accounts with one address become one.
- **Posts.** The importer turns BBCode into Markdown; `finish.rb` turns the card tag into
  `[[Card Name]]` and the discipline and clan smilies (`:pot:`, `:!bruj:`) into icon tags
  (`vekn.disciplines`, `vekn.clans`), deletes again what phpBB had hidden, and points in-post links to
  the old forum at their new topics. A post whose phpBB account was deleted stays the system user's.
  Private messages are not imported, since any admin of the site could read them, nor attachments
  and avatars, whose files the dump lacks.
- **Old URLs.** `/forum/viewforum.php?f=`, `/forum/viewtopic.php?t=` and `?p=` redirect to their
  category, topic and post on the site, through permalinks stored without `forum/` and the
  `permalink_normalizations` site setting the importer writes to strip it; `www.vekn.fr/forum/`
  does only once vekn.fr sends `/forum/` to it ([product.md#rollout](product.md#rollout)).

## Bridge

Configuration is read from the environment at point of use.

| variable | meaning |
|---|---|
| `BRIDGE_URL` | Its public origin; `<BRIDGE_URL>/callback` is the archon redirect URI. |
| `BRIDGE_SECRET` | Signs the login session cookie. |
| `DATABASE_URL` | Postgres holding the one table, `usernames`; the sweep reads it too. |
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
| `forum.krcg.org` | the bridge, whose root links every site |
| `intl.forum.krcg.org` | the international site: the launcher's default site, database `discourse`, `RAILS_DB=default` |
| `fr.forum.krcg.org` | the France site: database `discourse_fr`, `RAILS_DB=fr` |

A site is one entry in `SITES` in `deploy/deploy.py`. Its name must resolve to the host before a
deploy — the deploy refuses otherwise, since every failed Let's Encrypt validation counts against its
limit.

**Discourse** runs from its official launcher (`/var/discourse`, discourse_docker pinned in
`deploy.py`, Discourse at `discourse/ref`) as two containers, both written by the deploy: `data`
(Postgres and Redis for every site, `shared/data`) and `app` (every site's web and background
processes, `shared/web-only`). A change to `app.yml` bootstraps the new image while the old
container serves, then swaps them: the sites are down only while the new one starts. A change to
`data.yml` rebuilds the database, every site down meanwhile, and restarts `app`. The two-container
split is what makes the swap safe: a single container's bootstrap would start a second Postgres on
the live data. *(Decided 2026-09-26.)* Nothing is published: `data` is reached only through its
link from `app`, and `app`'s nginx listens on `/var/discourse/shared/web-only/nginx.http.sock`,
behind the host's nginx, which terminates TLS
(server-setup's `nginx_site`). For the sweep, `app` raises `DISCOURSE_MAX_ADMIN_API_REQS_PER_MINUTE`,
exempts the host's own address from the per-IP limits — counted across every site together — and
leaves out the launcher's nginx rate limit, which has no exemption. It sends mail through Gmail
SMTP as `codex.of.the.damned@gmail.com`, and makes
`DISCOURSE_DEVELOPER_EMAILS` admin: the break-glass login at `/u/admin-login`. Each site's settings, theme
and tokens come from `discourse/site.rb`, re-run whenever it, the site's values, `theme/` or the
site's `discourse/sites/<site>/` change, or the database is new: its marker lives in `shared/data`.
The deploy syncs `theme/` and `discourse/sites/` to `shared/web-only`.

**The bridge** runs as `vekn-forum-bridge` (uvicorn on `127.0.0.1:8030`, user `vekn_forum`, database
`vekn_forum` on the host cluster by peer auth), its environment in `/etc/vekn_forum/bridge.env`.
`vekn-forum-sweep.timer` runs the sweep hourly; the deploy runs it once more whenever a site is
provisioned, since it creates the role groups a login names.

**Backups.** The bridge's database is in the host's nightly Postgres backup. Each Discourse site
writes its own daily archive — database and uploads — under
`/var/discourse/shared/web-only/backups/<db>/`, and `vekn-forum-discourse-backup.timer` pushes
that directory to the fleet's restic bucket, repo `vekn_forum_discourse`. To restore one site:
`restic restore` the archive, drop it in that directory, then
`cd /var/discourse && ./launcher enter app`, `discourse enable_restore`, and
`RAILS_DB=<db> discourse restore <file>`.

**Secrets** (`just secrets`): `bridge_secret`, `mail_password`, per site `<site>_connect_secret` and
`<site>_api_key` (the deploy gives both to the site and to the bridge), and
`archon_client_id`/`archon_client_secret` — the one archon client of the Bridge table, with
`https://forum.krcg.org/callback` as redirect URI.

**Production logs in through archon beta** (`archon.krcg.org`, API `api.archon.krcg.org`), set in
`deploy.py`, until archon production carries `profile:email`: its client is registered on beta.
*(Decided 2026-09-26: open the forum now rather than wait on an archon production release.)*
