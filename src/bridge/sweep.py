"""Re-push what the bridge owns to every site, without a login: a role revoked in archon drops
admin and groups at the next sweep (wiki/engine.md#login). Run by a timer; `vekn-bridge-sweep`."""

import asyncio
import logging

from . import archon, discourse

logger = logging.getLogger("bridge.sweep")


async def sweep() -> None:
    """Every user is tried: one failure must not hold up everyone else's revocation."""
    token = await archon.daemon_token()
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
                await push(site, user_id, token)
            except Exception:
                failed = True
                logger.exception("%s: user %s failed", site, user_id)
    if failed:
        raise SystemExit(1)


async def push(site: str, user_id: int, token: str) -> None:
    detail = await discourse.user(site, user_id)
    record = detail.get("single_sign_on_record")
    if not record:
        return  # a local account (the operator's), not archon's
    uid = record["external_id"]
    member = await archon.member(uid, token)
    roles = member.get("roles", [])
    await discourse.sync(site, await discourse.rights(site, uid, roles, member.get("country")))
    await discourse.admit(site, detail, roles)
    logger.info("%s: synced %s", site, uid)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    asyncio.run(sweep())
