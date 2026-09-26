---
name: product
description: The product lens — make VTES community management effortless for NCs and Princes, on clean, mobile-first, noise-free screens. `/product scout` hunts time-savers in their recurring jobs; `/product audit <surface>` runs a keep/cut/merge subtraction pass at phone width. Also the gate /intake and /ship apply to any user-facing change. Use when designing, reviewing or questioning anything a user sees, or when looking for what to build next.
---

# /product — less, and the right less

The verdicts live in the wiki: personas and their recurring jobs in `wiki/product.md#personas`, the
design brief and the cut list in `wiki/design.md`. Read both first. This skill is the method; it
never holds a verdict of its own.

Two forces, always together: **push** what saves an NC or a Prince time, and **cut** what serves
no one. A pass that only adds, or only removes, has done half the job.

## The gate

Applied by `/intake` to any user-facing item and by `/ship` before a user-facing change lands.
Answer each in one line:

1. **Which persona job does it serve?** Name it from `product.md#personas`. None → refuse it, or,
   if it reveals a real recurring job, propose adding the job first (a scope change for the human).
2. **Is it the shortest path?** Count taps from the console or the page where the job starts.
   More than two for a recurring NC/Prince job, or anything the platform already knows being asked
   again, is a defect of the design, not a detail.
3. **What does it add to the screen, and what can go?** New element → name the one it replaces or
   why none can. Duplication with anything already on screen → remove one.
4. **Does it hold at 393 px?** Before landing: a screenshot at 393×852 (Chrome browser tools,
   `resize_window`), first viewport showing the work, touch targets ≥ 44 px.

## `/product scout`

Hunt time-savers. For each persona, NC and Prince first:

1. Walk each recurring job end to end on the real platform (or, before it runs, on Discourse's
   behaviour as documented) — count taps, screens, fields, context switches (forum → mail → chat).
2. Name the friction: a step the platform could prefill from archon or from what it already holds,
   an act split across tools that could be one, a job that needs Discourse admin.
3. Look outward for shortcuts other community tools give organisers — only those that would serve
   a named job here.
4. Also name jobs that are **missing** from `product.md#personas` — what an NC or Prince does
   often that nobody listed.

Output: a short ranked list, biggest time saved first, each with the job, the friction, the
proposed shortcut and its cost. The human picks; each accepted item goes through `/intake`, and a
new job lands in `product.md#personas`.

## `/product audit <surface>`

Subtraction pass over one surface: a page, a Discourse settings area, the theme, a flow.

1. Screenshot it at 393×852, then at desktop width.
2. List every element on it. For each, a verdict: **keep** (names the job it serves), **cut** (serves
   none, or is niche), **merge** (duplicates another element — say which survives), **move** (serves
   a job, wrong place or wrong prominence).
3. For Discourse features, the default is off: a feature stays only if a job claims it.

Output: the verdict table, then the proposed changes. Cuts accepted by the human are recorded in
`wiki/design.md#cut` with a one-line reason, so no one re-enables them by accident; the work goes
through `/intake`.

## Judgement

- A niche feature is one only a few members of one persona would use, rarely. Niche is a cut even
  when it is cheap: every element taxes every reader.
- Configurability is not a feature. A setting an NC must understand to get a sane result is a
  default we failed to choose.
- Prefer one act that does three things (post + mail + chat push) over three screens that each do
  one well.
- Consistency across sites beats per-site novelty; identity is tokens (`design.md#theming`).
