# Operations

Local dev, checks, CI and deploy.

**No checks yet** — no code has landed. Until it does, a board line's done-condition is verified by
hand and named in the line.

**Two deploy shapes.** Discourse runs from its official Docker launcher (multisite) on a dedicated
host — the one exception to the `server-setup` pattern, forced by the engine ([engine.md](engine.md)).
Everything we write (the login bridge) follows `server-setup`: pyinfra, systemd, nginx, the shared
Postgres cluster.
