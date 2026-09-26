---
name: product
description: The product lens — make VTES community management effortless for NCs and Princes, on clean, mobile-first, noise-free screens. `/product scout` hunts time-savers in their recurring jobs; `/product audit <surface>` runs a keep/cut/merge subtraction pass at phone width. Also the gate /intake and /ship apply to any user-facing change. Use when designing, reviewing or questioning anything a user sees, or when looking for what to build next.
---

# /product — less, and the right less

Every verdict lives in the wiki: personas and their recurring jobs in `wiki/product.md#personas`,
the design brief, its numbers and the cut list in `wiki/design.md`. Read both first. This skill is
the method only; where it needs a number or a rule, it points there.

Two forces, always together: **push** what saves an NC or a Prince time, and **cut** what serves
no one. A pass that only adds, or only removes, has done half the job.

## The gate

`/intake` applies questions 1–3 to any user-facing item; `/ship` applies all four before a
user-facing change lands. One line each:

1. **Which persona job does it serve?** Name it from `product.md#personas`. None → refuse it, or,
   if it reveals a real recurring job, propose adding the job first (a scope change for the human).
   A legal or operational obligation (privacy notice, security, backups) is exempt; say which.
2. **Is it the shortest path?** Against `design.md#time-savers-land-first`: count taps from where
   the job starts, and flag anything the platform already knows being asked again.
3. **What does it add to the screen, and what can go?** New element → name the one it replaces or
   why none can. Duplication with anything already on screen → remove one.
4. **Does it hold on a phone?** Screenshot the changed surface at the viewport in
   `design.md#mobile-first` (Chrome browser tools, `resize_window`) and check it against that
   section. Save it under the scratchpad; `/ship` passes its path to the egress reviewer.

## `/product scout`

Hunt time-savers. For each persona, NC and Prince first:

1. Walk each recurring job end to end on the real platform (or, before it runs, on Discourse's
   behaviour as documented) — count taps, screens, fields, context switches (forum → mail → chat).
2. Name the friction: a step the platform could prefill from archon or from what it already holds,
   an act split across tools that could be one, a job that needs Discourse admin.
3. Look outward for shortcuts other community tools give organisers — only those that would serve
   a named job here.
4. Also name jobs **missing** from `product.md#personas` — what an NC or Prince does often that
   nobody listed.

Output: a short ranked list, biggest time saved first, each with the job, the friction, the
proposed shortcut and its cost. The human picks; each accepted item goes through `/intake`, and a
new job lands in `product.md#personas`.

## `/product audit <surface>`

Subtraction pass over one surface: a page, a Discourse settings area, the theme, a flow.

1. Screenshot it at the `design.md#mobile-first` viewport, then at desktop width.
2. List every element on it. For each, a verdict: **keep** (names the job it serves), **cut**,
   **merge** (duplicates another — say which survives), **move** (right job, wrong place or
   prominence). On stock Discourse screens, the means are settings and the base theme only
   (`dogmas.md#engine`).
3. Discourse features follow `design.md#less-is-more`.

Output: the verdict table, then the proposed changes. The human decides; accepted cuts go to
`design.md#cut`, the work through `/intake`.
