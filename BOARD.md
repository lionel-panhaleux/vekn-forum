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
- Ban suspends everywhere — an active Ethics Ban in archon (a `suspension` with no end date) suspends the member on every site through the bridge, at login and by the sweep, and lifting it unsuspends; the bridge reads it from `/v1/users/{uid}` with its `api:read` token, the only audience archon gives sanctions to. Waits on archon-vibe's queued line exposing active suspensions and probations to `api:read` clients (chase, 3 Oct). Doc-impact: engine.md, archon.md.
- France phpBB import — obtain a phpBB database dump from the vekn.fr administrators (chase, 3 Oct) and import it into the local fr site: topic and post counts match phpBB, legacy `viewtopic.php` URLs redirect. Doc-impact: engine.md, operations.md.
- Base theme and France identity — the shared base theme (remote git) with a component turning `[[Card Name]]` into a card image on hover (images from krcg), installed on the local sites; fr tokens set on the fr site. Doc-impact: design.md, engine.md.
- Tournament mirror — each upcoming archon tournament of a country appears as a topic in its site's tournaments category, updated when archon changes it. Doc-impact: engine.md, archon.md.
- Privacy notice — every site links a GDPR notice naming the controller, what is held (archon uid, email, posts, IP logs) and retention. Doc-impact: product.md.
- Console — a plugin page where each coordinator and section-lead job in `wiki/product.md#personas` meets `wiki/design.md#time-savers-land-first` and `#mobile-first`, contents fixed by a first `/product scout`. Doc-impact: design.md, product.md, engine.md.
- Production host — ask Lionel before renting or touching DNS: a dedicated Docker host runs the fr and international sites on platform subdomains, with backups. Doc-impact: operations.md.
- Listmonk — self-hosted per server-setup; every list mirrors a Discourse group, kept in sync by the bridge; a coordinator or section lead manages only their groups' lists. Doc-impact: product.md, engine.md, operations.md.

<!-- cycles-since-upkeep: 2 -->
