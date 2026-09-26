"""The Discourse sites: DiscourseConnect payloads, the rights the bridge owns, and the admin API.

Each site is configured from `DISCOURSE_<SITE>_*` — wiki/operations.md lists them.
"""

import base64
import datetime
import hashlib
import hmac
import os
import urllib.parse

import httpx

#: One group per archon role, named in lower case (wiki/engine.md#login).
ROLES = ["IC", "NC", "Prince", "Ethics", "PTC", "PT", "Rulemonger", "Judge", "Sheriff", "DEV"]
#: A language group carries the prefix of the roles that gate it; the bridge removes, never adds.
LANGUAGE_GATES = {"pt-": {"PT", "PTC"}, "judge-": {"Judge", "Rulemonger"}}


def sites() -> list[str]:
    return os.getenv("DISCOURSE_SITES", "").split()


def env(site: str, key: str, default: str | None = None) -> str:
    value = os.getenv(f"DISCOURSE_{site.upper()}_{key}", default)
    if value is None:
        raise KeyError(f"DISCOURSE_{site.upper()}_{key}")
    return value


def sign(site: str, payload: str) -> str:
    secret = env(site, "SECRET").encode()
    return hmac.new(secret, payload.encode(), hashlib.sha256).hexdigest()


def decode(site: str, sso: str, sig: str) -> dict[str, str]:
    """A login request from `site`, or ValueError when it was not signed with that site's secret."""
    if not hmac.compare_digest(sign(site, sso), sig):
        raise ValueError("bad signature")
    return dict(urllib.parse.parse_qsl(base64.b64decode(sso).decode()))


def encode(site: str, fields: dict[str, str]) -> dict[str, str]:
    sso = base64.b64encode(urllib.parse.urlencode(fields).encode()).decode()
    return {"sso": sso, "sig": sign(site, sso)}


def admitted(site: str, roles: list[str]) -> bool:
    """`DISCOURSE_<SITE>_MEMBERS` lists the roles a gated site (playtest) admits; unset is open."""
    gate = env(site, "MEMBERS", "")
    return not gate or bool(set(gate.split(",")) & set(roles))


def is_admin(site: str, roles: list[str], country: str | None) -> bool:
    """`DISCOURSE_<SITE>_ADMINS`: comma-separated `ROLE` or `ROLE@COUNTRY` — `NC@FR`, `IC`, `PTC`."""
    for rule in env(site, "ADMINS", "").split(","):
        role, _, scope = rule.partition("@")
        if role and role in roles and (not scope or scope == country):
            return True
    return False


async def rights(site: str, uid: str, roles: list[str], country: str | None) -> dict[str, str]:
    """What the bridge owns, sent whole every time: `admin` is applied only when present, and
    only named groups are touched — never `groups`, which would strip the site's own."""
    held = {r.lower() for r in roles}
    remove = [r.lower() for r in ROLES if r.lower() not in held]
    for prefix, gate in LANGUAGE_GATES.items():
        if not gate & set(roles):
            remove += await groups(site, prefix)
    return {
        "external_id": uid,
        "admin": "true" if is_admin(site, roles, country) else "false",
        "add_groups": ",".join(r.lower() for r in ROLES if r.lower() in held),
        "remove_groups": ",".join(remove),
    }


def suspend_reason(site: str) -> str:
    """The bridge lifts only the suspensions it made, told apart by this exact reason."""
    return f"archon: holds none of {env(site, 'MEMBERS')}"


async def api(site: str, method: str, path: str, **kwargs) -> dict:
    headers = {"Api-Key": env(site, "API_KEY"), "Api-Username": "system"}
    async with httpx.AsyncClient(base_url=env(site, "URL"), timeout=30) as client:
        response = await client.request(method, path, headers=headers, **kwargs)
    response.raise_for_status()
    return response.json()


async def sync(site: str, fields: dict[str, str]) -> dict:
    """Push a payload to an existing user without a login."""
    return await api(site, "POST", "/admin/users/sync_sso", data=encode(site, fields))


async def create_role_groups(site: str) -> None:
    """A payload naming a group that does not exist is silently ignored by Discourse."""
    existing = set(await groups(site, ""))
    for name in [r.lower() for r in ROLES if r.lower() not in existing]:
        await api(site, "POST", "/admin/groups.json", data={"group[name]": name})


async def groups(site: str, prefix: str) -> list[str]:
    names, page = [], 0
    while True:
        data = await api(site, "GET", "/groups.json", params={"filter": prefix, "page": page})
        batch = [g["name"] for g in data["groups"]]
        names += [n for n in batch if n.startswith(prefix)]
        if not batch or not data.get("load_more_groups"):
            return names
        page += 1


async def user_ids(site: str) -> set[int]:
    """Whoever the bridge may have to take rights from: admins, role and language group members,
    and on a gated site every user, since admission itself can be lost."""
    lists = ["active"] if env(site, "MEMBERS", "") else ["admins"]
    ids = set()
    for query in lists:
        page = 1
        while batch := await api(
            site, "GET", f"/admin/users/list/{query}.json", params={"page": page}
        ):
            ids |= {u["id"] for u in batch}
            page += 1
    names = [r.lower() for r in ROLES]
    for prefix in LANGUAGE_GATES:
        names += await groups(site, prefix)
    for name in names:
        offset = 0
        while True:
            data = await api(
                site,
                "GET",
                f"/groups/{name}/members.json",
                params={"limit": 1000, "offset": offset},
            )
            ids |= {u["id"] for u in data["members"]}
            offset += 1000
            if offset >= data["meta"]["total"]:
                break
    return {i for i in ids if i > 0}


async def user(site: str, user_id: int) -> dict:
    return await api(site, "GET", f"/admin/users/{user_id}.json")


async def by_external_id(site: str, uid: str) -> dict | None:
    try:
        return (await api(site, "GET", f"/u/by-external/{uid}.json"))["user"]
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return None
        raise


async def username_for_email(site: str, email: str) -> str | None:
    """The existing account a login will be linked to by email (a legacy phpBB author)."""
    found = await api(site, "GET", "/admin/users/list/all.json", params={"email": email})
    return found[0]["username"] if found else None


async def admit(site: str, detail: dict, roles: list[str]) -> None:
    """On a gated site, suspend a member who lost admission and lift what the bridge suspended
    once it is regained. A suspension made by a moderator is never touched. `detail` is the
    user as `user()` reads it."""
    if not env(site, "MEMBERS", ""):
        return
    user_id = detail["id"]
    until = detail.get("suspended_till")
    # An expired suspension keeps its date.
    suspended = bool(until) and datetime.datetime.fromisoformat(until) > datetime.datetime.now(
        datetime.UTC
    )
    ours = detail.get("full_suspend_reason") == suspend_reason(site)
    if admitted(site, roles):
        if suspended and ours:
            await api(site, "PUT", f"/admin/users/{user_id}/unsuspend")
    elif not suspended:
        await api(
            site,
            "PUT",
            f"/admin/users/{user_id}/suspend",
            data={"suspend_until": "3000-01-01", "reason": suspend_reason(site)},
        )
