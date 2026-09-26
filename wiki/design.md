# Design

The standing design brief, applied by `/product` and checked at ingress and egress. We design for
the **NC and the Prince first** — their recurring jobs are in [product.md#personas](product.md#personas)
— and for members second. Principles shared with archon are borrowed from archon-vibe's
`wiki/design.md` (2026-09-26) so a member moving between the two apps finds the same logic.

## Less is more

**Every element earns its place by serving a persona job.** What serves none is cut, not hidden
behind a setting. On Discourse this is mostly subtraction: its defaults are **off until a job
claims them**, and a cut is recorded below with its one-line reason.

**Nothing twice.** One home per action and per piece of information on a screen — the same button
in a header and a menu, the same count in a badge and a title, the same hint in a banner and a
field label are all duplication to remove. Guidance names a control once, by its real label.

**The rendered change is the confirmation.** No success toast where the screen already shows the
outcome. A confirm step only for irreversible or outward-facing acts (a mail to a whole list, a
deletion), naming the undo where there is one.

**One primary action per screen.** The rest collapses into an overflow menu.

**Consistency across sites beats per-site novelty.** Identity is tokens, not layout (below).

## Time-savers land first

**A recurring NC or Prince job is at most two taps from the console** ([below](#nc-console)), and
never needs Discourse's admin panel. Prefill everything the platform already knows — archon's
tournament, the playgroup's venue, the community's lists — rather than asking. A wizard fronts a
form, it never replaces one.

## Mobile first

Designed at **393×852** first, then enhanced for desktop.

- 44×44 px minimum touch targets.
- **The first viewport shows the work**: a list reaches its first rows without scrolling; filters
  fold behind one control naming how many are active.
- Modal heights in `dvh`, never `vh`; edge-anchored surfaces absorb the safe-area insets.
- Checked by a screenshot at 393 px wide before a user-facing change lands.

## Theming

**One shared base theme plus per-site tokens.** *(Decided 2026-09-26.)* The base theme owns layout,
components and interactions, maintained once. A site's identity is only its tokens: logo, palette
(with its light/dark pair), accent, icon set, optionally a heading font. A need a token cannot
express is a change to the base theme, for every site.

## NC console

**A single mobile-first page, from our plugin, for the NC's and Prince's recurring jobs.**
*(Decided 2026-09-26.)* Discourse's admin stays reachable for the rare rest. Its contents are exactly
the jobs in [product.md#personas](product.md#personas) — a job added there is a job the console
serves.

## Cut

| Feature | Why |
|---|---|
| Discourse chat | Chat lives in WhatsApp, Telegram and Discord ([product.md](product.md)). |
