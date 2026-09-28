# Post-deploy — checks a deploy unlocks

A board line is **done when it is reviewed and committed**. What only a deployed environment can
prove — archon answering, a site serving, a production setting — is not part of its
done-condition: it parks here, and the line is deleted on landing like any other.

One `##` section per check. It names the **gating commit** (and its repo, when that is not this one),
where to run, what to run, and what proves it worked. **Completion is deletion**; an empty page is the
normal state.

When the human says a deploy is live, run every section it gates. A pass deletes the section; a
failure is new work and goes through `/intake`.

A check that belongs to a sibling repo's own deploy lives on that repo's post-deploy page, not here —
archon's are on `vtes-biased/archon-vibe` `wiki/post-deploy.md`.

## Log in through archon and sweep against it

Gated by the commit that first deploys production ("Deploy the fr and international sites and the
bridge to frankfurt"). The local tests prove the bridge against a stand-in; this proves the same
contract against the archon the deploy names (beta for now: `archon.krcg.org`, public API
`api.archon.krcg.org`). It needs the vekn-forum client registered there by an IC or DEV from Developer with `profile:email` **and**
`api:read` checked (one client serves both the login and the sweep), its purpose stated, and
`https://forum.krcg.org/callback` as redirect URI; its id and secret go in `just secrets`.

In a browser, open `https://fr.forum.krcg.org/session/sso?return_path=/session/current.json` as a
member holding NC with country FR, then the same path on `intl.forum.krcg.org`; on frankfurt,
`sudo systemctl start vekn-forum-sweep` and `journalctl -u vekn-forum-sweep`.

It worked when the consent page names the forum's email purpose, both logins land on a JSON
`current_user`, that user is admin on fr and not on intl (the site's Admin → Users), and the sweep
finishes without an archon error — its daemon token accepted by archon's public API.

## The production host serves and backs up

Gated by the same commit. On frankfurt:
`https://fr.forum.krcg.org` and `https://intl.forum.krcg.org` render their site, in French and
English; `/u/admin-login` on either mails a login link to the developer email. The morning after the
first deploy, `ls /var/discourse/shared/web-only/backups/*/` lists one archive per site, and
`sudo systemctl status vekn-forum-discourse-backup` shows a push to `vekn_forum_discourse`, with no
orphan warning for it in `journalctl -t postgres-backup`.

## A ban in archon suspends on every site

Gated by the commit "Suspend a member archon bans on every site, and lift it with the ban", and
by archon beta running v1.2.8 (`api.archon.krcg.org/openapi.json` names `sanctions`). The local tests
prove it against a stand-in; this proves archon's `sanctions` shape and that it reaches the bridge's
daemon token.

On archon beta, as Ethics, give a test member holding a VEKN ID and accounts on fr and intl a
suspension with no end date. In a private window, log in on `https://fr.forum.krcg.org` as that
member; on frankfurt, `sudo systemctl start vekn-forum-sweep`. Then lift the sanction in archon and
start the sweep again.

It worked when the login lands on the bridge's "Membership suspended" page, the member shows as
suspended on both sites (Admin → Users → Suspended) with reason `archon: banned by the VEKN` after
the first sweep, and is unsuspended on both after the second.

## The fr site wears France's identity, and shows cards

Gated by the commits "Theme every site from a shared base, and dress fr in France's tokens", "Give
sections VEKN icons, and members a light/dark toggle" and "Show every section in the sidebar,
unfolded, and switch chat off", "Give members the sections through Discourse's default sidebar list" and "Add a cards-and-icons picker to every composer's toolbar".
In a browser with its interface in French, open `https://fr.forum.krcg.org` in light and dark
system mode, then post `[[Anson]] et [[Diriger les indécis]]`
in a test topic, then open a reply, tap the toolbar's cards button and type `Sang`.

It worked when the header is black with the V:EKN wordmark over a red rule, the tab shows the red
V, dark mode keeps a red (not pink) accent, and hovering each name shows its scan — the second in
French; on a phone, a tap shows it and another dismisses it. The picker lists French card names for `Sang` over a narrowed icon grid, and a pick lands in the
reply. The sidebar's foot has the light/dark toggle, and a category set to a `vekn-*` icon in its
settings shows it in the accent. Neither site's categories page lists General, Site Feedback or
Uncategorized. Logged out and logged in, the sidebar lists every section unfolded in the categories
page's order, with no "all categories" link, still after opening your own profile's activity, and
no chat bubble or chat section shows.
`https://intl.forum.krcg.org` wears the base palettes.

## No site downloads Inter

Gated by the commit "Read every site in the device's own font". On `https://fr.forum.krcg.org` and
`https://intl.forum.krcg.org`, list the fonts the palette stylesheets declare:
`curl -s --compressed -H 'Accept: text/html' <site>/latest`, then each `color_definitions_*.css` it
links, grepped for `/fonts/`.

It worked when neither names `InterVariable`, fr still names `PlayfairDisplay`, and a phone's first
visit to fr shows body text in its system font (San Francisco, Roboto) under Playfair headings.
