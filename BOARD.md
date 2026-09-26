# Board

What must change. The goal is zero. **Completion is deletion** — no closed state, no archive; git
history is the record. Context lives in [`wiki/`](wiki/index.md), never here: a line that cannot be
completed is documentation, and belongs on a wiki page instead.

**Order is priority**, and priority is decided by these rules, top down:

1. **Blocks someone else** — another person, another repo, another line.
2. **User-visible breakage.**
3. **User-visible feature.**
4. **Internal cleanup.**

Ties break to the smaller line. An item waiting on someone is not a state: it is a dated
follow-up ("chase @lip, 12 Sep"), owned by whoever wrote it.

---
- archon `email` scope — in archon-vibe (its own `/intake`: overturns its never-share-emails policy): archon beta `/oauth/userinfo` returns the verified address, never the address of record, under a consent-gated `email` scope whose consent text says what the forum does with it. Blocks the bridge. Doc-impact: archon.md.
- Login bridge, proven locally — a two-site local Discourse (fr + international) and the bridge against archon beta: a beta login creates the user; an imported user with the same email is linked, not duplicated; an NC gets admin on their own site only; revoking the role in archon drops admin through `sync_sso` without a login; an active Ethics Ban in archon suspends the user on every site and lifting it unsuspends (needs archon to expose ban status to the bridge). Doc-impact: engine.md, operations.md (bridge stack and checks), dogmas.md (framework idioms).
- France phpBB import — obtain a phpBB database dump from the vekn.fr administrators (chase, 3 Oct) and import it into the local fr site: topic and post counts match phpBB, legacy `viewtopic.php` URLs redirect. Doc-impact: engine.md, operations.md.
- Base theme and France identity — the shared base theme (remote git) with a component turning `[[Card Name]]` into a card image on hover (images from krcg), installed on the local sites; fr tokens set on the fr site. Doc-impact: design.md, engine.md.
- Tournament mirror — each upcoming archon tournament of a country appears as a topic in its site's tournaments category, updated when archon changes it. Doc-impact: engine.md, archon.md.
- Privacy notice — every site links a GDPR notice naming the controller, what is held (archon uid, email, posts, IP logs) and retention. Doc-impact: product.md.
- NC console — a plugin page where each NC and Prince job in `wiki/product.md#personas` meets `wiki/design.md#time-savers-land-first` and `#mobile-first`, contents fixed by a first `/product scout`. Doc-impact: design.md, product.md, engine.md.
- Production host — ask Lionel before renting or touching DNS: a dedicated Docker host runs the fr and international sites on platform subdomains, with backups. Doc-impact: operations.md.
- Listmonk — self-hosted per server-setup; community lists fed by the bridge, each NC managing only their community's lists; role lists (judges for Rulemongers, playtesters by language for PTCs) synced from archon, which needs archon to hand role holders' emails to a trusted daemon client and to model a playtest language. Doc-impact: product.md, archon.md, operations.md.

<!-- cycles-since-upkeep: 0 -->
