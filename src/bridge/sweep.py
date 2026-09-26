"""Re-push what the bridge owns to every site, without a login: a role revoked in archon drops
admin and groups at the next sweep, a ban suspends everywhere (wiki/engine.md#login). Run by a
timer; `vekn-bridge-sweep`."""

import asyncio
import logging
from collections.abc import Awaitable, Callable

from . import archon, db, discourse

logger = logging.getLogger("bridge.sweep")
#: Seconds between archon lookups: 400 a minute of the 600 archon grants a client, the rest left
#: to logins, which spend the same budget.
PACE = 0.15

Lookup = Callable[[str], Awaitable[dict]]


async def sweep() -> None:
    """Every user is tried: one failure must not hold up everyone else's revocation."""
    token = await archon.daemon_token()
    members: dict[str, dict] = {}

    async def lookup(uid: str) -> dict:
        """Once per member per sweep, however many sites they are on."""
        if uid not in members:
            await asyncio.sleep(PACE)
            members[uid] = await archon.member(uid, token)
        return members[uid]

    failed = False
    for site in discourse.sites():
        try:
            await discourse.create_role_groups(site)
            user_ids = sorted(await discourse.user_ids(site))
        except Exception:
            failed = True
            logger.exception("%s: failed", site)
            continue
        for user_id in user_ids:
            try:
                await push(site, user_id, lookup)
            except Exception:
                failed = True
                logger.exception("%s: user %s failed", site, user_id)
    # A ban can fall on anyone who ever logged in, not only on those the sites list above.
    async with await db() as conn:
        rows = await (await conn.execute("SELECT archon_uid FROM usernames")).fetchall()
    for (uid,) in rows:
        try:
            if not archon.banned(await lookup(uid)):
                continue
            for site in discourse.sites():
                if found := await discourse.by_external_id(site, uid):
                    await push(site, found["id"], lookup)
        except Exception:
            failed = True
            logger.exception("member %s failed", uid)
    if failed:
        raise SystemExit(1)


async def push(site: str, user_id: int, lookup: Lookup) -> None:
    detail = await discourse.user(site, user_id)
    record = detail.get("single_sign_on_record")
    if not record:
        return  # a local account (the operator's), not archon's
    uid = record["external_id"]
    member = await lookup(uid)
    roles = member.get("roles", [])
    await discourse.sync(site, await discourse.rights(site, uid, roles, member.get("country")))
    await discourse.standing(site, detail, roles, archon.banned(member))
    logger.info("%s: synced %s", site, uid)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    asyncio.run(sweep())
