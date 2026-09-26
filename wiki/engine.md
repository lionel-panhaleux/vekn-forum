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

**DiscourseConnect** behind our own small bridge service; with it on, Discourse disables every
other login (local, email link, OAuth) except `/u/admin-login` for admins. The bridge runs the
archon PKCE flow, reads `country` from archon's public API, and signs each site a payload:

- `external_id` = archon uid; `email` = the **verified** address from archon's `email` scope
  ([archon.md](archon.md) — pending, see the board). The bridge passes it through and stores none.
- **Never `require_activation`, never an unverified email.** Discourse links a new `external_id` to
  an existing user by email only without it — that match *is* the legacy claim. With it, the match
  is skipped and a legacy address fails as a duplicate; an unverified email without it would hand
  a stranger the legacy account. A member with no verified email in archon is sent to archon to add
  one.
- `username` = a **suggestion** only, the member's preferred handle, asked once on first login and
  the one thing the bridge stores. `auth_overrides_username` stays off: each site owns its
  usernames, a claimed account keeps its phpBB name, and a collision gets a numeric suffix the
  member can rename.
- `admin` and the **role groups** (one per archon role, e.g. `nc`, `prince`, `judge`).

The bridge owns exactly four things: `admin`; the role groups; **admission to the playtest site** —
it refuses a playtest payload without PT or PTC, and suspends there a member who loses both; and
**removal from language groups** when the role that gates them is lost — `pt-*` needs PT or PTC, `judge-*` needs Judge or
Rulemonger; it finds them through the Discourse API by that prefix, so a language group must carry
it. Archon decides who may be in a language group, its owner decides which language. Coordinators
delegate through moderators and section groups, never by granting admin. The bridge sends only
`add_groups`/`remove_groups` for the names it owns, never the full `groups` list. Rights are re-pushed through `sync_sso`, not only at login, so a revoked NC loses admin
without logging in again. The same archon login creates the user on any site on first visit, so
one user table per site stays invisible.

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
