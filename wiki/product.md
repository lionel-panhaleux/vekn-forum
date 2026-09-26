# Product

A shared, modern forum platform for VEKN national communities, replacing the per-association phpBB
silos ([community.md](community.md)). Members log in with their archon account
([archon.md](archon.md)); archon roles decide who runs what.

## Personas

Every community has a **coordinator** who administers it and **section leads** under them:

| Community | Coordinator | Sections | Section lead |
|---|---|---|---|
| National | NC | playgroups (city, shop, bar night) | Prince |
| International | IC | topics, and the judges' section | Rulemonger for the judges, by language |
| Playtest | PTCs (all admins) | languages | the PTC owning that language |

Recurring jobs, most frequent first. The console serves the coordinator's and section lead's
([design.md#console](design.md#console)); a user-facing change that serves none of them is cut at
ingress. *(Decided 2026-09-26.)*

- **Coordinator** — announce to the whole community in one act (post, mail, chat push); open a
  section and appoint its lead; welcome a newcomer and route them to the right section; handle
  flags; pin the major events; adjust the site's identity (rare).
- **Section lead** — announce to the section (post, mail, chat push): a play night, a tournament, a
  new playtest round, rulings news; keep the section's members, venue, schedule and chat links
  current; welcome newcomers; moderate the section.
- **Member** — find the nearest playgroup and its chat; see upcoming tournaments; ask a rules or
  beginner question, and read the cards a post names; trade; recover their old posts; follow only
  the sections in their language.

## Scope

- **One deployment, one site per community**: each national community, the international community,
  and the playtest community. **A role community gets its own site only when its content is
  confidential** — playtest (NDA) does; the judges are a section of the international site. Each
  site has its **own graphical identity** — logo, colours, icons, styles — so it reads as that
  community's forum, optionally under the association's own domain. *(Decided 2026-09-26.)*
- **Coordinators administer their community** (personas above): they configure its identity,
  sections and moderators without being platform admins; section leads run their section. The
  platform owns sections and the section lead → section assignment (Prince → playgroup, language
  lead → language group), since archon roles have no scope below the country
  ([archon.md#roles](archon.md#roles)).
- **Adopt an existing open-source forum engine** rather than building one. It must support external
  OAuth, have a genuinely good interface, allow CSS theming and some JS (VTES card display, icons),
  and be self-hosted: **Discourse multisite**, one site per community ([engine.md](engine.md)).
  *(Decided 2026-09-26.)*
- **phpBB archives are imported**: boards, topics and posts under their legacy authors. Claiming is
  automatic when the archon email matches; otherwise the coordinator merges. Login must stay as fluid as
  possible — for most members, one archon consent screen and nothing else. *(Decided 2026-09-26.)*

- **Public read, archon posts** — except the playtest site, readable only by PT and PTC holders and
  never indexed. Elsewhere anyone can read and search engines index; any archon account may
  post, VEKN ID or not, so newcomers can ask. A site may gate private categories (association board,
  organizers) by group. *(Decided 2026-09-26.)*
- **Tournaments come from archon.** Each upcoming archon tournament is mirrored as a topic in its
  country's tournaments category and kept current from archon; discussion and reports live in that
  thread. *(Decided 2026-09-26.)*
- **Chat apps get pushes and links.** Discourse's chat-integration plugin pushes chosen categories
  to a community's Discord and Telegram, configured by the coordinator; WhatsApp is a link only (no usable
  group API). *(Decided 2026-09-26.)*
- **Mailing lists and newsletters run on Listmonk**, self-hosted beside Discourse. **Every list
  mirrors a Discourse group** — a community, a section (playgroup, language) —
  kept in sync by the login bridge, so mailing a group is the same act everywhere. Discourse's own
  mail (notifications, digests) stays on. *(Decided 2026-09-26.)*

- **Playgroups are categories.** Each playgroup is a category led by its Prince; its description
  carries venue, schedule and chat links; the site's category list is the directory. archon's
  country-level community links show in the site sidebar only. *(Decided 2026-09-26.)*
- **Anti-spam is archon's signup plus Discourse defaults** — trust levels and the flag review queue
  worked by the coordinator and moderators; no approval queue. *(Decided 2026-09-26.)*

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
- **New sites: the coordinator asks, the operator creates**, batched into maintenance windows — not
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
