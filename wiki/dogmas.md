# Dogmas

Paradigms chosen by the human. Ingress challenges an incoming ask against this page; egress checks
the landed change against it. Overturning one is valid work; violating one silently is not.
Code, Testing, Commits and Human inflexion points are carried over from the sibling VEKN repos
(rulings-website, krcg-bot) on 2026-09-26 and stand until the human overturns them.

## Data

**Facts have one home.** Identity, roles, VEKN IDs and country are archon's
([archon.md](archon.md)); card data is krcg's. We copy a fact only where the copy is rewritten from
its owner on every login or refresh — never edited locally, never trusted stale.

## Engine

**The engine is upstream; we configure, we don't fork.** In order of preference: engine settings,
an official or well-maintained plugin, our own plugin or theme component through the engine's
public extension points (Discourse plugins, theme components, DiscourseConnect). Patching or forking
Discourse core is a rejection. Our own code is the glue only: the login bridge, the base theme and its
components, the console plugin, import tooling, deploy. *(2026-09-26.)*

## Code

**Tight, local, KISS.** No patterns, abstractions or indirection for elegance's sake — they must earn
their keep. Don't write for a human reader's comfort; keep it terse for agentic workers.

**Locality first.** Co-locate what changes together; keep files readable in one pass. Extract a
module only behind an interface much narrower than what it hides. Layering ceremony — clean-arch,
hexagonal — is an anti-pattern here: it mass-produces shallow modules, which are pure token cost and
misuse surface.

**KISS means hazard-avoidance, not small diffs.** Big rewrites are cheap; the coding loop is agentic
and rewrites fast. What is expensive is *hazard* — non-local interdependency, behaviour not evident
where it lives, traps for a future agent without today's context. Prefer the design a fresh agent
can understand from the files in front of it. The amount of code needing a rewrite is never a reason
to defer.

**Repetition over false abstraction.** Similar-looking but causally unrelated code stays repeated.
Never factor on resemblance.

**Comments are for traps only.** The wiki holds the why, the code shows the how. A comment is
justified only by a subtle non-local constraint invisible at the point of reading. No narration, no
changelogs, **no TODOs** — discovered work goes through ingress or gets done now.

**Framework idioms as they come** — the engine's own inside its extension points (Ruby and Ember
for Discourse plugins and theme components); a service we run ourselves, such as the login bridge,
is Python 3.13 with FastAPI and uv, like the sibling VEKN services, because `server-setup` deploys
nothing else. Configuration read from the environment at point of use, never a settings object.

## Testing

**Few tests, high coverage of behaviour.** Test what the product does at its boundaries — the API,
the CLI, end-to-end nominal paths and the failure modes that matter — never how it does it. Agents
don't make local mistakes, they make non-local ones: unit tests of internals calcify implementation
and tax every change, while integration and non-regression tests catch what matters and survive
refactors.

- A test is the executable slice of this wiki: each must trace to a declared behaviour. One that maps
  to no wiki claim is evicted.
- **Mocks are banned by default** — a mock that mirrors the code tests the code against itself. Use
  real dependencies (a real engine instance, a real Postgres, temp files) or don't test that path.
  archon is the exception: tests run against a local stand-in server that speaks its documented
  contract ([archon.md](archon.md)) over HTTP, as rulings-website does, since archon beta cannot be
  scripted into role changes; beta itself is proven after deploy ([post-deploy.md](post-deploy.md)).
- Exception: property-style tests for genuinely hazardous invariants (parsing, concurrency) — the
  same spots KISS flags.
- **Weakening or deleting a test is an egress rejection** unless the wiki-declared behaviour changed.


## Dependencies

Prefer what the engine already offers, then a few lines, then a dependency. krcg is the exception in
the other direction: anything about cards belongs upstream in krcg, not reimplemented here.

## Commits and branches

**Trunk-based**: commit straight to `main`, fast-forward, no feature branches. Two or three agents
may work parallel board lines on `main` — each claims its line, stays aware of siblings, keeps to its
own commits; imperfect commit isolation is acceptable when files overlap.

Describe the change itself in the message. **GitHub** issue numbers are the exception: when a commit
fixes a known GitHub issue, close it with a `Fixes #N` line just above the trailers.

## Human inflexion points

Interrupt the human only for: a dogma or paradigm choice (short option set plus a recommendation), an
irreversible or outward-facing action, a genuine change to product scope, accepting, reordering or
dropping a board line, or an egress deadlock after
two rounds. Everything else proceeds. HitL effort goes into the harness, not the code — the ratchet
turns a correction into a standing rule.
