# Design

The standing design brief, applied by `/product` and checked at ingress and egress. We design for
**coordinators and section leads first** — their recurring jobs are in [product.md#personas](product.md#personas)
— and for members second. Principles shared with archon are borrowed from archon-vibe's
`wiki/design.md` (2026-09-26) so a member moving between the two apps finds the same logic.

## Less is more

**Where these rules bind.** On our own surfaces — the console, the base theme — fully. On stock
Discourse screens, only through settings and the base theme: subtract there, never patch core
([dogmas.md#engine](dogmas.md#engine)).

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

**Niche is a cut even when it is cheap** — a feature only a few members of one persona would use,
rarely, taxes every reader. **Configurability is not a feature**: a setting a coordinator must understand
to get a sane result is a default we failed to choose.

**Consistency across sites beats per-site novelty.** Identity is tokens, not layout (below).

## Time-savers land first

**A recurring coordinator or section-lead job is at most two taps from the console** ([below](#console)) once
the console exists, and never needs Discourse's admin panel. One act that does three things
(post, mail, chat push) beats three screens that each do one well. Prefill everything the platform
already knows — archon's tournament, the playgroup's venue, the community's lists — rather than
asking. A wizard fronts a
form, it never replaces one.

## Mobile first

Designed at **393×852** first, then enhanced for desktop.

- 44×44 px minimum touch targets.
- **The first viewport shows the work**: a list reaches its first rows without scrolling; filters
  fold behind one control naming how many are active.
- Modal heights in `dvh`, never `vh`; edge-anchored surfaces absorb the safe-area insets.

## Theming

**One shared base theme plus per-site tokens.** *(Decided 2026-09-26.)* The base theme owns layout,
components and interactions, maintained once. A site's identity is only its tokens: title, logo and
small mark, a palette pair (light and dark, the accent being the palette's `tertiary`), optionally a
heading font from Discourse's list. Tokens are Discourse's own settings, not theme settings
([engine.md](engine.md#model-mapping)); a site without its own wears the base palettes, archon's. Their one home is `discourse/sites/<site>/`: a coordinator's rare identity change is a change there, since the next provisioning rewrites an edit made in Discourse's admin.
Components every site needs, such as VTES card display, belong to the base theme. A need a token
cannot express is a change to the base theme, for every site.

A site follows the device's light or dark mode; a member can pin either from the toggle at the foot of
the sidebar, as in archon.

The base theme's one mark is a rule in the accent colour under the header. Text in an accent passes
WCAG AA (4.5:1) against its palette's background: France's dark accent is a lighter red than its
light one for that reason.

**Card display.** `[[Card Name]]` in a post, English or translated, shows the card's scan — in the
site's language when krcg has it — on hover where the device hovers, and on tap (dismissed by
another) otherwise. A name krcg does not know stays as typed; code and links are left alone.

## Category icons

**A category's icon names its kind of section, the same on every site**; the base theme's sprite
(`theme/assets/icons.svg`) draws them as filled silhouettes beside VTES's own symbols. A category
takes its kind's icon, drawn in the palette's accent whatever the category's colour, so it follows
light and dark: the icons tell sections apart, not colours. A new kind of section is a new
icon here, for every site. Every icon is in the category icon picker of every site, under `vekn`.

**A new site starts with its sections.** A site's identity (`discourse/sites/<site>/identity.json`)
lists them in order, each a name in the site's language and a slug naming its kind in English, as
code stays English; the slug gives the icon. Provisioning creates them while the site has no
category of its own besides Uncategorized and Staff; after that they are the coordinator's, so a
renamed, reordered or deleted section stays so. Staff keeps Discourse's permissions, admins and
moderators, and takes its own icon.

| Kind of section | Icon | Figure |
|---|---|---|
| Announcements | `vekn-announcements` | herald's trumpet |
| Game, strategy, decks | `vekn-game` | two library cards, a discipline diamond |
| Newcomers | `vekn-newcomers` | a blood drop — the Embrace |
| Rules | `vekn-rules` | codex marked with an ankh |
| Tournaments | `vekn-tournaments` | the Prince's crown |
| Trading | `vekn-trading` | coins stamped with an ankh |
| Regions and playgroups | `vekn-regions` | a domain's skyline |
| International (English) | `vekn-international` | compass star |
| Association | `vekn-association` | the political action symbol |
| Off-topic | `vekn-offtopic` | the tavern goblet |
| Archives | `vekn-archives` | a coffin — torpor |
| Playtest | `vekn-playtest` | masquerade mask |
| Judges | `vekn-judges` | Auspex's eye |

## Sidebar

| Staff | `vekn-staff` | Ventrue's sword and sceptre |
**Every section is in the sidebar, unfolded, in the coordinator's order**, for visitors and members
alike, while a site has at most 15 top-level sections: nothing to open to find one, and no per-
member list to curate. The categories page stays reachable from the list's tabs (a dropdown on a
phone), so the sidebar drops its link to it. Past 15, Discourse's own sidebar returns, each member's
saved list with it.

## Console

**A single mobile-first page, from our plugin, for the coordinator's and section lead's recurring
jobs**, on every site.
*(Decided 2026-09-26.)* Discourse's admin stays reachable for the rare rest. Its contents are exactly
the coordinator and section-lead jobs in [product.md#personas](product.md#personas) — one added there is one
the console serves.

## Cut

The home for every Discourse feature we switch off.

| Feature | Why |
|---|---|
| Discourse chat | Not a chat platform ([product.md#deliberately-not](product.md#deliberately-not)). |
| "Powered by Discourse" footer | Serves no persona job. |
| Choosing another theme | Consistency across sites; the base theme is the only selectable one. |
| Stock categories (General, Site Feedback) | Every category is a section; removed while only the system has posted in them. |
| Uncategorized topics | A topic belongs to a section; Discourse's Uncategorized stays, empty and unlisted. |
