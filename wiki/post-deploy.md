# Post-deploy — checks a deploy unlocks

A board line is **done when it is reviewed and committed**. What only a deployed environment can
prove — archon beta answering, a site serving, a production setting — is not part of its
done-condition: it parks here, and the line is deleted on landing like any other.

One `##` section per check. It names the **gating commit** (and its repo, when that is not this one),
where to run, what to run, and what proves it worked. **Completion is deletion**; an empty page is the
normal state.

When the human says a deploy is live, run every section it gates. A pass deletes the section; a
failure is new work and goes through `/intake`.

A check that belongs to a sibling repo's own deploy lives on that repo's post-deploy page, not here —
archon's are on `vtes-biased/archon-vibe` `wiki/post-deploy.md`.
