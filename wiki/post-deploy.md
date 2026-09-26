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

## The production host serves, hides its container and backs up

Gated by the same commit. On frankfurt: `sudo ss -ltnp` shows no port held by `docker-proxy`;
`https://fr.forum.krcg.org` and `https://intl.forum.krcg.org` render their site, in French and
English; `/u/admin-login` on either mails a login link to the developer email. The morning after the
first deploy, `ls /var/discourse/shared/standalone/backups/*/` lists one archive per site, and
`sudo systemctl status vekn-forum-discourse-backup` shows a push to `vekn_forum_discourse`, with no
orphan warning for it in `journalctl -t postgres-backup`.
