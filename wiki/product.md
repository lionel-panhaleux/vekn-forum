# Product

A shared, modern forum platform for VEKN national communities, replacing the per-association phpBB
silos ([community.md](community.md)). Members log in with their archon account
([archon.md](archon.md)); archon roles decide who runs what.

## Personas

Recurring jobs, most frequent first. The NC console serves the NC and Prince ones
([design.md#nc-console](design.md#nc-console)); a user-facing change that serves none of them is
cut at ingress. *(Proposed 2026-09-26.)*

- **NC** — announce to the whole community in one act (post, mail, chat push); open a playgroup
  and appoint its Prince; welcome a newcomer and route them to the nearest playgroup; handle flags;
  pin the national events; adjust the site's identity (rare).
- **Prince** — announce the next play night or tournament to the playgroup (post plus chat push);
  keep the playgroup's venue, schedule and chat links current; welcome newcomers; moderate the
  section.
- **Role-list sender** (PTC, Rulemonger) — mail their list: playtesters in a language, judges.
- **Member** — find the nearest playgroup and its chat; see upcoming tournaments; ask a rules or
  beginner question, and read the cards a post names; trade; recover their old posts.

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

- **Playgroups are categories.** Each playgroup is a category led by its Prince; its description
  carries venue, schedule and chat links; the site's category list is the directory. archon's
  country-level community links show in the site sidebar only. *(Decided 2026-09-26.)*
- **Anti-spam is archon's signup plus Discourse defaults** — trust levels and the flag review queue
  worked by the NC and moderators; no approval queue. *(Decided 2026-09-26.)*

- **An archon Ban suspends everywhere.** A member under an active Ethics Ban sanction in archon is
  suspended on every site; lifting it lifts the suspension. *(Decided 2026-09-26.)*
- **GDPR.** Every site shows a privacy notice naming the controller (Lionel, while he runs it), what
  is held and why; archon's consent screen for the `email` scope says what the forum does with the
  address. *(Decided 2026-09-26.)*

## Rollout

- **France pilots**: its import, legacy-account claiming and identity are proven at full scale on one
  site before other communities are offered one. *(Decided 2026-09-26.)*
- **Domains**: every site has a platform subdomain; an association may point its own domain at its
  site, which also carries its old phpBB URL redirects. *(Decided 2026-09-26.)*
- **Ownership**: runs on Lionel's infra and account for now, to be handed to VEKN if it takes.
  *(Decided 2026-09-26.)*
- **New sites: the NC asks, the operator creates**, batched into maintenance windows — not
  self-service, because adding a site restarts every site of the multisite; a web form would own
  that. *(Decided 2026-09-26.)*
- **vekn.net's forum** may later be offered to VEKN for import into the international site
  (Discourse ships a Kunena importer), once the France pilot proves the pattern. VEKN's call.
  *(Decided 2026-09-26.)*

## Deliberately not

- **Not a chat platform.** Chat groups live in WhatsApp, Telegram and Discord; Discourse's built-in
  chat is cut ([design.md#cut](design.md#cut)). *(Decided 2026-09-26.)*
- **Not a mail server.** Outgoing mail goes through an SMTP relay.
- **Not a source of identity or roles.** Those are archon's.
