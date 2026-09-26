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

Gated by the commit that first lands the bridge (`src/bridge/`, "Build the archon login bridge…"),
and on archon's side by the release carrying `profile:email` reaching production. The local tests
prove the bridge against a stand-in; this proves the same contract against archon production
(`archon.vekn.net`, public API `api.archon.vekn.net`). It needs the vekn-forum client registered
there by an IC or DEV from Developer with `profile:email` **and** `api:read` checked (one client
serves both the login and the sweep), its purpose stated, and `http://localhost:8765/callback` as
redirect URI.

Run the local stack (`just discourse`), then the bridge against archon:
`set -a; . .local/discourse.env; set +a; BRIDGE_URL=http://localhost:8765 BRIDGE_SECRET=… ARCHON_CLIENT_ID=… ARCHON_CLIENT_SECRET=… uv run uvicorn bridge:app --port 8765`.
In a browser, open `http://fr.localhost:3000/session/sso?return_path=/session/current.json` as a
member holding NC with country FR, then `http://intl.localhost:3000/session/sso?return_path=/session/current.json`;
then run `uv run vekn-bridge-sweep` with the same environment.

It worked when the consent page names the forum's email purpose, both logins land on a JSON
`current_user`, that user is admin on fr and not on intl (`/admin/users/list/admins.json` with the
site's API key), and the sweep finishes without an archon error — its daemon token accepted by
`api.archon.vekn.net`.
