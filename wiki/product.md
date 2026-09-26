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
  night). The platform owns sections and the Prince → section assignment ([archon.md#roles](archon.md#roles)).
- **Adopt an existing open-source forum engine** rather than building one. It must support external
  OAuth, have a genuinely good interface, allow CSS theming and some JS (VTES card display, icons),
  and be self-hosted: **Discourse multisite**, one site per community ([engine.md](engine.md)).
  *(Decided 2026-09-26.)*
- **phpBB archives are imported**: boards, topics and posts under their legacy authors. Claiming is
  automatic when the archon email matches; otherwise the NC merges. Login must stay as fluid as
  possible — for most members, one archon consent screen and nothing else. *(Decided 2026-09-26.)*

- **Public read, archon posts.** Anyone can read and search engines index; any archon account may
  post, VEKN ID or not, so newcomers can ask. A site may gate private categories (association board,
  organizers) by group. *(Decided 2026-09-26.)*
- **Tournaments come from archon.** Each upcoming archon tournament is mirrored as a topic in its
  country's tournaments category and kept current from archon; discussion and reports live in that
  thread. *(Decided 2026-09-26.)*
- **Chat apps get pushes and links.** Discourse's chat-integration plugin pushes chosen categories
  to a community's Discord and Telegram, configured by the NC; WhatsApp is a link only (no usable
  group API). *(Decided 2026-09-26.)*
- **Mailing lists and newsletters run on Listmonk**, self-hosted beside Discourse, its subscribers
  fed by the login bridge from archon-verified emails. Beyond communities, it serves **role lists**
  synced from archon: judges for Rulemongers, playtesters by language for PTCs. Discourse's own mail (notifications, digests)
  stays on. *(Decided 2026-09-26.)*

## Rollout

- **France pilots**: its import, legacy-account claiming and identity are proven at full scale on one
  site before other communities are offered one. *(Decided 2026-09-26.)*
- **Domains**: every site has a platform subdomain; an association may point its own domain at its
  site, which also carries its old phpBB URL redirects. *(Decided 2026-09-26.)*
- **Ownership**: runs on Lionel's infra and account for now, to be handed to VEKN if it takes.
  *(Decided 2026-09-26.)*

## Deliberately not

- **Not a chat platform.** Chat groups live in WhatsApp, Telegram and Discord; Discourse's built-in
  chat stays off. *(Decided 2026-09-26.)*
- **Not a mail server.** Outgoing mail goes through an SMTP relay.
- **Not a source of identity or roles.** Those are archon's.
