# Engine

**Discourse, in multisite mode.** *(Decided 2026-09-26.)* The only open-source engine where each
community is truly its own forum administered by its coordinator, with a maintained phpBB importer that
keeps old URLs alive, and the best interface of the field. NodeBB fits our no-Docker infra better
but offers only per-category branding under global admins and no maintained importer; that is the
alternative a future agent will be tempted to redo — the identity requirement is what rules it out.

## Model mapping

| Ours | Discourse |
|---|---|
| National community (France, Germany, …) | One **site** of the multisite: own database, theme, locale, settings, admins, domain. |
| International community | Its own site. |
| Playtest community | Its own site, NDA content isolated in its own database. Two locks: the bridge admits only PT and PTC holders to it, and every category's security grants the `pt` and `ptc` role groups only, `everyone` removed. `login_required`, not indexed. |
| Coordinator | `admin` on their community's site: an NC on the site of their archon `country`, ICs on the international site, **every PTC** on the playtest site. *(Decided 2026-09-26.)* |
| Section | A category (subcategories for cities under a region), plus its **section group**, which watches the category's first posts by default. Playgroup groups are open to join; language groups (`pt-fr`, `judge-fi`, …) are added to by their owner only, and their category is visible to that group alone. |
| Section lead | Owner of the section group, and in the category's moderating group — both set by the coordinator. Owning a group needs no admin. |
| Judges | A section of the international site, moderated by Rulemongers; its language groups are created by an IC. |
| Role-wide English section (playtest, judges) | Visible to the whole role group, muted by default through that group's default notification levels: opt-in. |
| Base theme, card display | One remote git theme with its components, installed on every site and updated from git. |
| Community identity | That theme's settings on each site: the tokens of [design.md#theming](design.md#theming). |
| Legacy phpBB author | User from the phpBB3 importer, email kept; claimed as below. |

## Login

**DiscourseConnect** behind our own small bridge service (`src/bridge/`); with it on, Discourse
disables every other login (local, email link, OAuth) except `/u/admin-login` for admins. The bridge
runs the archon PKCE flow with `profile:email`, reads `country` and sanctions from archon's public
API (`/v1/users/{uid}` with its own `api:read` token, since userinfo has neither and only that token
is told sanctions), and signs each site a payload:

- `external_id` = archon uid; `email` = the **verified** address from archon's `profile:email`
  scope ([archon.md](archon.md)). The bridge passes it through and stores none. Every site sets
  `auth_overrides_email` (the address is rewritten from archon on each login) and therefore
  `email_editable` off, which Discourse requires for it: a member changes their email in archon.
- `locale` = the language the bridge spoke to the member, which Discourse applies only when it
  creates the account; after that the member's own choice stands. Every site sets
  `set_locale_from_accept_language_header` and its `default_locale`; the bridge's own pages speak
  the browser's first language it has, else English. Discourse cannot narrow its preferences'
  language menu, so every locale it ships stays selectable there. With no browser language the
  bridge speaks, `locale` is left out and the site's default applies.
- **Never `require_activation`, never an unverified email.** Discourse links a new `external_id` to
  an existing user by email only without it — that match *is* the legacy claim. With it, the match
  is skipped and a legacy address fails as a duplicate; an unverified email without it would hand
  a stranger the legacy account. A member with no verified email in archon is sent to archon to add
  one.
- `username` = a **suggestion** only, the member's preferred handle, asked once on first login and
  the one thing the bridge stores. A member whose email already matches an account on the site
  they log into (a legacy author) is not asked: that account's name becomes their stored handle.
  `auth_overrides_username` stays off: each site owns its usernames, a claimed account keeps its
  phpBB name, and a collision gets a numeric suffix the member can rename.
- `admin`, sent `true` or `false` on every payload — Discourse applies it only when present — and
  the **role groups**, one per archon role named in lower case (`ic`, `nc`, `prince`, `ethics`,
  `ptc`, `pt`, `rulemonger`, `judge`, `sheriff`, `dev`). Discourse validates group names as
  usernames, so every site sets `min_username_length` to 2; groups must exist before a payload
  names them, or Discourse ignores them, so the sweep (below) creates any that is missing.

The bridge owns exactly five things: `admin`; the role groups; **admission to the playtest site** —
it refuses a playtest login without PT or PTC, and suspends there a member who loses both; **the
VEKN ban** ([product.md](product.md#scope)) — a member archon holds an Ethics ban against (a
`suspension` with no end date) is refused at login and suspended on every site where they have an
account, and lifting the ban in archon lifts it; and **removal from language groups** when the role
that gates them is lost — `pt-*` needs PT or PTC, `judge-*` needs Judge or Rulemonger; it finds them
through the Discourse API by that prefix, so a language group must carry it. Archon decides who may
be in a language group, its owner decides which language. The bridge lifts only suspensions
carrying one of its own two reasons, a ban's outranking the gate's, so regaining PT while banned
lifts nothing; a moderator's suspension is never touched. A member with no VEKN ID has no public API
row, so a ban on them stays invisible to the bridge. Coordinators delegate through moderators and
section groups, never by granting admin. The bridge sends only
`add_groups`/`remove_groups` for the names it owns, never the full `groups` list.

The bridge's own root lists every site, in the browser's language, so the platform address leads
somewhere.

The Coordinator row above is per-site configuration of the bridge ([operations.md](operations.md#bridge)).

**Rights are re-pushed without a login.** A sweep (`vekn-bridge-sweep`, on a timer) reads every
site's admins, suspended users, role- and language-group members — every user, on the playtest site
— and every member who ever logged in (the `usernames` table), for bans; it takes their
roles and country from archon's public API with the bridge's own `api:read` token, and pushes them
through `sync_sso`, so a revoked NC loses admin without logging in again. It looks each member up
once per run, paced under archon's per-client lookup budget, which logins share, so a run lasts at
least the pace times the members who ever logged in and must stay under the timer's period. The bridge keeps no
refresh token. Its burst of admin API calls needs Discourse's rate limit raised
([operations.md](operations.md#deploy)). The same archon login creates the user on any site on first visit, so one
user table per site stays invisible.

**Claiming a legacy account.** Imported phpBB users keep their email, so a member whose archon
email matches is linked on first login — posts and username included, nothing to click. The email
match relinks even a user already linked to another archon uid; archon's unique addresses keep
that from happening. A dead legacy address, or a guest-post placeholder (`anonymous_users`,
`@no-email.invalid`), is merged by the site's coordinator through Discourse's admin user merge, which moves
posts, quotes and mentions.

## Accepted costs

- Docker is mandatory for Discourse ([operations.md](operations.md) holds the hosting).
- The Discourse team does not support self-hosted multisite configuration; all sites share plugins
  and upgrade together.

Sources: discourse/discourse `app/models/discourse_connect.rb` (`match_email_or_create_user`,
`change_external_attributes_and_override`), `app/controllers/session_controller.rb`
(`check_local_login_allowed`), `lib/user_merger.rb`; meta.discourse.org/t/14084 (multisite),
github.com/discourse/discourse `script/import_scripts/phpbb3.rb`, `docs/INSTALL-cloud.md`; checked
2026-09-26.
