# Product

A shared, modern forum platform for VEKN national communities, replacing the per-association phpBB
silos ([community.md](community.md)). Members log in with their archon account
([archon.md](archon.md)); archon roles decide who runs what.

## Scope

- **One deployment, one space per community.** Each national community gets its own space with its
  **own graphical identity** — logo, colours, icons, styles — so it reads as that association's
  forum, optionally under the association's own domain. Cross-community sections (international,
  English) live on the same platform. *(Decided 2026-09-26.)*
- **NCs administer their space**: they configure its identity, sections and moderators without being
  platform admins. Princes lead playgroup sections inside it (a city, a shop's regular play, a bar
  night). archon scopes roles by country only, so the platform owns sections and the Prince →
  section assignment.
- **Adopt an existing open-source forum engine** rather than building one. It must support external
  OAuth, have a genuinely good interface, allow CSS theming and some JS (VTES card display, icons),
  and be self-hosted: **Discourse multisite**, one site per community ([engine.md](engine.md)).
  *(Decided 2026-09-26.)*
- **phpBB archives are imported**: boards, topics and posts under their legacy authors. A legacy
  account is claimable — linked to an archon login once confirmed. *(Decided 2026-09-26.)*

## Deliberately not

- **Not a chat platform.** Chat groups live in WhatsApp, Telegram and Discord; the platform links to
  and at most integrates with them. *(Decided 2026-09-26.)*
- **Not a mail server.** Mailing lists go through a third-party tool that is open-source, free or
  self-hosted. *(Decided 2026-09-26.)*
- **Not a source of identity or roles.** Those are archon's.
