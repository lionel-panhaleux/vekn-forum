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
- Archon production — the production bridge logs in through archon production (`archon.vekn.net`): `deploy.py` stops naming archon beta, a production client is registered with `profile:email` and `api:read` and in `just secrets`, and the post-deploy login check re-runs against production. Waits on archon production deploying `profile:email` (chase, 27 Sep). A member first seen on beta relinks by email on their first production login. Doc-impact: operations.md, post-deploy.md.
- France phpBB import — obtain a phpBB database dump from the vekn.fr administrators (chase, 3 Oct) and import it into the local fr site: topic and post counts match phpBB, legacy `viewtopic.php` URLs redirect, its card markup (rendered by krcg.js as `span.krcg-card`) becomes `[[Card Name]]`, and each category wears its kind's icon ([design.md#category-icons](wiki/design.md#category-icons)). Doc-impact: engine.md, operations.md.
- Tournament mirror — each upcoming archon tournament of a country appears as a topic in its site's tournaments category, updated when archon changes it. Doc-impact: engine.md, archon.md.
- Privacy notice — every site links a GDPR notice naming the controller, what is held (archon uid, email, posts, IP logs) and retention. Doc-impact: product.md.
- Console — a plugin page where each coordinator and section-lead job in `wiki/product.md#personas` meets `wiki/design.md#time-savers-land-first` and `#mobile-first`, contents fixed by a first `/product scout`. Doc-impact: design.md, product.md, engine.md.
- Listmonk — self-hosted per server-setup; every list mirrors a Discourse group, kept in sync by the bridge; a coordinator or section lead manages only their groups' lists. Doc-impact: product.md, engine.md, operations.md.

<!-- cycles-since-upkeep: 9 -->
