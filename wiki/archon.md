# archon

The VEKN membership and tournament system, and our only identity provider. Identity, roles and
country are archon's facts; we copy one only where the copy is rewritten from archon on read.
Source for every claim below: the archon-vibe wiki (`vtes-biased/archon-vibe`, `wiki/access.md`,
`wiki/public-api.md`, `wiki/discord.md`, `wiki/vekn.md`), read 2026-09-26, and the working client in
`vtes-biased/rulings-website` (`wiki/auth.md`).

## Hosts

Prod `archon.vekn.net`, beta `archon.krcg.org`. Separate databases: an OAuth client is registered on
each. Public API at `api.<domain>` (prod pending its first deploy as of 2026-09-26).

## OAuth2 provider

Plain OAuth2 (RFC 6749) with **PKCE S256 required**. **Not OIDC**: no id_token, no discovery document,
no JWKS. Off-the-shelf "OIDC login" plugins do not apply; a generic OAuth2 client pointed at
`userinfo` does.

- Entry: send the browser to `<ARCHON>/consent?response_type=code&client_id=…&redirect_uri=…&scope=profile:read&state=…&code_challenge=…&code_challenge_method=S256`.
  Not to `/oauth/authorize`, which answers JSON `{redirect_url}`, never a 302.
- `/oauth/token` (form or JSON body), `/oauth/revoke` (RFC 7009 — kills the whole rotation lineage),
  `/oauth/userinfo`.
- Confidential clients: secret plus PKCE verifier; exact `redirect_uri` match. Registered by an IC or
  DEV on archon's Developer page; the secret is shown once.
- Tokens: EdDSA JWTs, 1 h access, 30 d refresh, **rotating** — replaying a spent refresh token revokes
  the chain. Two concurrent refreshes with one token log the user out everywhere.
- Scopes: `profile:read` reaches `/oauth/*` only. `api:read` is the `client_credentials` daemon grant
  (1 h JWT, no refresh) for the public API.

## What a login tells us

`/oauth/userinfo` → `{sub, roles, vekn_id, capabilities}`. **No name, no email, no country.**

- `sub` is the archon uid — the stable key. `vekn_id` may be absent (unsponsored member).
- The user's `country` (ISO alpha-2) comes from public API `GET /v1/users/{uid}`, which accepts the
  user's own token at any scope. Never a name: archon publishes VEKN IDs, never names, to third
  parties.
- NC and Prince contact emails are not exposed to the API.

## Roles

IC, NC, Prince, Ethics, PTC, PT, Rulemonger, Judge, Sheriff, DEV. Any role requires a `vekn_id`.

- **Roles carry no scope.** Scoping is the holder's `country`: an NC acts on their own country. Prince
  is described as city-level but archon knows no city scope — only a free-text `city` on the user.
- NCs appoint Princes in their country; IC appoints NCs.
- archon's capabilities are all archon-domain; none is forum-shaped. Clients match role strings.

## Events and geography

- Tournaments: `country`, `timezone`, dates, `state`, free-text `venue`/`address`/`map_url`,
  `registration_url`, `online`, `league_uid`, organizers. No city field, **no venue or playgroup
  entity**.
- Public API `GET /v1/tournaments?country=&start_after=&start_before=`, `leagues`, `community-links`:
  bearer token required (daemon or user), JSON Lines, no pagination.
- iCal: `/api/calendar/tournaments.ics?country=XX`, upcoming only.
- **Community links** (Discord, Instagram, …, each with a country and languages, NC/IC moderated) are
  archon's closest thing to a playgroup directory.

## Discord and messaging

Discord OAuth is an archon login method and account link; **Linked Roles** push role levels (Member,
Prince, NC, IC) so Discord servers can gate channels without a bot. archon has no Telegram, WhatsApp,
mailing-list or newsletter feature — those exist only as community-link types. Its email is
transactional only.

## Proven client pattern (rulings-website)

`/login` → `/login/callback`; access token treated as opaque; user row upserted on `archon_uid`;
roles re-read **hourly** with the stored refresh token under a conditional UPDATE so exactly one
request spends it; a 400 from archon is final and drops the token, ending that user's sessions.

## vekn.net

Decommission is VEKN's call and unscheduled; end state is archon as system of record with vekn.net
frozen as an archive. Nothing in archon's plan covers the vekn.net forum.
