"""Re-push what the bridge owns to every site, without a login: a role revoked in archon drops
admin and groups at the next sweep (wiki/engine.md#login). Run by a timer; `vekn-bridge-sweep`."""

import asyncio
import logging

from . import archon, discourse

logger = logging.getLogger("bridge.sweep")


async def sweep() -> None:
    token = await archon.daemon_token()
    for site in discourse.sites():
        for user_id in sorted(await discourse.user_ids(site)):
            detail = await discourse.user(site, user_id)
            record = detail.get("single_sign_on_record")
            if not record:
                continue  # a local account (the operator's), not archon's
            uid = record["external_id"]
            member = await archon.member(uid, token)
            roles = member.get("roles", [])
            await discourse.sync(
                site, await discourse.rights(site, uid, roles, member.get("country"))
            )
            await discourse.admit(site, detail, roles)
            logger.info("%s: synced %s", site, uid)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    asyncio.run(sweep())
