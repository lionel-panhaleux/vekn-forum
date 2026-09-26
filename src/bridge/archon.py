"""archon OAuth2 client — wiki/archon.md. PKCE login, userinfo, and the public API for country
and sanctions."""

import base64
import hashlib
import os
import urllib.parse

import httpx

TIMEOUT = 10


class Error(Exception):
    def __init__(self, message: str, status: int = 0):
        #: 0 is a transport failure; anything else is archon's own status.
        self.status = status
        super().__init__(message)


def app_url() -> str:
    return os.getenv("ARCHON_URL", "https://archon.vekn.net").rstrip("/")


def api_url() -> str:
    """The public API lives on its own host; userinfo does not exist there."""
    return os.getenv("ARCHON_API_URL", "https://api.archon.vekn.net").rstrip("/")


def redirect_uri() -> str:
    """archon matches it exactly, so it is registered verbatim."""
    return os.environ["BRIDGE_URL"].rstrip("/") + "/callback"


def authorization_url(state: str, verifier: str) -> str:
    """archon's frontend consent page, which forwards its query to /oauth/authorize verbatim."""
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    params = {
        "response_type": "code",
        "client_id": os.environ["ARCHON_CLIENT_ID"],
        "redirect_uri": redirect_uri(),
        "scope": "profile:email",
        "state": state,
        "code_challenge": base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii"),
        "code_challenge_method": "S256",
    }
    return f"{app_url()}/consent?{urllib.parse.urlencode(params)}"


async def exchange_code(code: str, verifier: str) -> str:
    """The access token only: the bridge never refreshes, so it drops the refresh token."""
    data = await _request(
        "POST",
        f"{app_url()}/oauth/token",
        json={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri(),
            "code_verifier": verifier,
            "client_id": os.environ["ARCHON_CLIENT_ID"],
            "client_secret": os.environ["ARCHON_CLIENT_SECRET"],
        },
    )
    return data["access_token"]


async def daemon_token() -> str:
    """`api:read` client_credentials: reads members' roles, country and sanctions — the only token
    archon tells sanctions to."""
    data = await _request(
        "POST",
        f"{app_url()}/oauth/token",
        json={
            "grant_type": "client_credentials",
            "scope": "api:read",
            "client_id": os.environ["ARCHON_CLIENT_ID"],
            "client_secret": os.environ["ARCHON_CLIENT_SECRET"],
        },
    )
    return data["access_token"]


async def userinfo(token: str) -> dict:
    """`{sub, roles, vekn_id, capabilities}`, plus `email` when archon holds a verified one."""
    return await _request("GET", f"{app_url()}/oauth/userinfo", token=token)


async def member(uid: str, token: str) -> dict:
    """`{roles, country, …}` from the public API, plus `sanctions` to the daemon token only. A
    member with no VEKN ID is absent from it, and since every role requires one, absent means no
    roles, no country — and no ban the bridge can see."""
    try:
        return await _request("GET", f"{api_url()}/v1/users/{uid}", token=token)
    except Error as e:
        if e.status == 404:
            return {"roles": [], "country": None}
        raise


def banned(member: dict) -> bool:
    """An Ethics ban: a suspension with no end (wiki/product.md#scope)."""
    return any(
        s["level"] == "suspension" and s["expires_at"] is None for s in member.get("sanctions", [])
    )


async def _request(method: str, url: str, token: str | None = None, **kwargs) -> dict:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.request(method, url, headers=headers, **kwargs)
    except httpx.HTTPError as e:
        raise Error(f"{url}: {e!r}") from e
    if response.status_code != 200:
        raise Error(f"{url}: {response.status_code} {response.text[:200]}", response.status_code)
    return response.json()
