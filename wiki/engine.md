# Engine

**Discourse, in multisite mode.** *(Decided 2026-09-26.)* The only open-source engine where each
community is truly its own forum administered by its NC, with a maintained phpBB importer that
keeps old URLs alive, and the best interface of the field. NodeBB fits our no-Docker infra better
but offers only per-category branding under global admins and no maintained importer; that is the
alternative a future agent will be tempted to redo — the identity requirement is what rules it out.

## Model mapping

| Ours | Discourse |
|---|---|
| Community space (France, Germany, …) | One **site** of the multisite: own database, theme, locale, settings, admins, domain. |
| Cross-community space (international) | Its own site. |
| NC | `admin` on the site of their archon `country`. |
| Section / playgroup | A category (subcategories for cities under a region). |
| Prince leading a section | Member of the section's moderating group; the NC assigns it on their site. |
| VTES card display, icons | Theme components, per site. |
| Legacy phpBB author | Placeholder user from the phpBB3 importer, linked to an archon account when claimed. |

## Login

archon is plain OAuth2 with PKCE and gives no email or name ([archon.md](archon.md)), which no
Discourse login plugin handles whole. So login goes through **DiscourseConnect** backed by our own
small bridge service: it runs the archon PKCE flow, reads `country` from archon's public API, holds
the one fact archon lacks — the member's email — and hands each site a signed payload with
`external_id` = archon uid, `admin` and group membership derived from archon roles. The same archon
login creates the user on any site on first visit, so one user table per site stays invisible.
Roles are re-pushed by the bridge, not only at login, so a revoked NC loses admin without logging
in again.

## Accepted costs

- Docker is mandatory for Discourse; it runs on its own host outside the pyinfra/systemd pattern
  ([operations.md](operations.md)).
- The Discourse team does not support self-hosted multisite configuration; all sites share plugins
  and upgrade together.

Sources: meta.discourse.org/t/13045 (DiscourseConnect), /t/14084 (multisite),
github.com/discourse/discourse `script/import_scripts/phpbb3.rb`, `docs/INSTALL-cloud.md`; checked
2026-09-26.
