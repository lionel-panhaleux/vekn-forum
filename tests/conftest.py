"""The bridge between the real local Discourse sites (`just dev`) and a stand-in archon.

The stand-in speaks archon's documented contract (wiki/archon.md) over HTTP — consent, PKCE token
exchange, userinfo, `client_credentials`, `/v1/users/{uid}` with `sanctions` for the daemon token
alone — and nothing of the bridge's
internals. archon itself is proven after deploy (wiki/post-deploy.md).
"""

import base64
import hashlib
import os
import pathlib
import secrets
import socket
import subprocess
import threading
import time
import urllib.parse
import uuid

import httpx
import psycopg
import psycopg.sql
import pytest
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse

ENV = pathlib.Path(__file__).parent.parent / ".local" / "discourse.env"
if not ENV.exists():
    raise RuntimeError("no local Discourse: run `just dev` first")
for line in ENV.read_text().splitlines():
    key, _, value = line.partition("=")
    os.environ[key] = value.strip('"')
ARCHON = f"http://127.0.0.1:{8766}"
# Beside `just dev`'s bridge (8765, database `bridge`), so a test run disturbs neither its port nor its
# members' handles; the `archon` fixture points the sites' login at this bridge for the session.
BRIDGE_PORT = 8767
os.environ |= {
    "BRIDGE_URL": f"http://localhost:{BRIDGE_PORT}",
    "DATABASE_URL": os.environ["DATABASE_URL"].rpartition("/")[0] + "/bridge_test",
    "BRIDGE_SECRET": secrets.token_hex(16),
    "ARCHON_URL": ARCHON,
    "ARCHON_API_URL": ARCHON,
    "ARCHON_CLIENT_ID": "vekn-forum",
    "ARCHON_CLIENT_SECRET": secrets.token_hex(16),
}

# Only now: importing the bridge reads the environment set above.
import bridge
import bridge.discourse


class Archon:
    """Members by uid, and who is signed in to archon's own frontend right now."""

    def __init__(self):
        self.members: dict[str, dict] = {}
        self.signed_in: str | None = None
        self.codes: dict[str, tuple[str, str]] = {}
        self.tokens: dict[str, str] = {}
        self.app = FastAPI()
        self.app.get("/consent")(self.consent)
        self.app.post("/oauth/token")(self.token)
        self.app.get("/oauth/userinfo")(self.userinfo)
        self.app.get("/v1/users/{uid}")(self.user)

    def member(self, roles=(), country="FR", email: str | None = "", vekn_id="1000001") -> str:
        uid = str(uuid.uuid4())
        if email == "":
            email = f"{uid[:8]}@example.com"
        self.members[uid] = {
            "roles": list(roles),
            "country": country,
            "email": email,
            "vekn_id": vekn_id,
            "sanctions": [],
        }
        self.signed_in = uid
        return uid

    async def consent(self, request: Request):
        """The member has already consented once: archon redirects straight back."""
        q = request.query_params
        assert q["response_type"] == "code" and q["code_challenge_method"] == "S256"
        assert q["client_id"] == os.environ["ARCHON_CLIENT_ID"]
        assert q["redirect_uri"] == os.environ["BRIDGE_URL"] + "/callback"
        assert self.signed_in
        code = secrets.token_urlsafe()
        self.codes[code] = (self.signed_in, q["code_challenge"])
        query = urllib.parse.urlencode({"code": code, "state": q["state"]})
        return RedirectResponse(f"{q['redirect_uri']}?{query}", 302)

    async def token(self, request: Request):
        body = await request.json()
        if body["client_secret"] != os.environ["ARCHON_CLIENT_SECRET"]:
            raise HTTPException(401)
        if body["grant_type"] == "client_credentials":
            token = secrets.token_urlsafe()
            self.tokens[token] = ""
            return {"access_token": token, "token_type": "Bearer", "scope": "api:read"}
        uid, challenge = self.codes.pop(body["code"])
        digest = hashlib.sha256(body["code_verifier"].encode()).digest()
        if base64.urlsafe_b64encode(digest).rstrip(b"=").decode() != challenge:
            raise HTTPException(400, "PKCE verifier mismatch")
        token = secrets.token_urlsafe()
        self.tokens[token] = uid
        return {"access_token": token, "refresh_token": secrets.token_urlsafe(), "expires_in": 3600}

    def bearer(self, request: Request) -> str:
        token = request.headers.get("authorization", "").removeprefix("Bearer ")
        if token not in self.tokens:
            raise HTTPException(401)
        return self.tokens[token]

    async def userinfo(self, request: Request):
        m = self.members[self.bearer(request)]
        info = {"sub": self.bearer(request), "roles": m["roles"], "vekn_id": m["vekn_id"]}
        if m["email"]:
            info["email"] = m["email"]
        return info | {"capabilities": []}

    async def user(self, request: Request, uid: str):
        daemon = self.bearer(request) == ""
        m = self.members.get(uid)
        if not m or not m["vekn_id"]:
            raise HTTPException(404, "User not found")
        body = {"uid": uid, "vekn_id": m["vekn_id"], "country": m["country"], "roles": m["roles"]}
        return body | ({"sanctions": m["sanctions"]} if daemon else {})


def serve(app, port: int) -> None:
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    threading.Thread(target=server.run, daemon=True).start()
    while socket.socket().connect_ex(("127.0.0.1", port)):
        time.sleep(0.05)


async def point_login(site: str, bridge_url: str) -> None:
    """Point the site's login button (`discourse_connect_url`) at a bridge."""
    env = bridge.discourse.env
    async with httpx.AsyncClient(base_url=env(site, "URL"), timeout=30) as client:
        response = await client.put(
            "/admin/site_settings/discourse_connect_url",
            headers={"Api-Key": env(site, "API_KEY"), "Api-Username": "system"},
            data={"discourse_connect_url": f"{bridge_url}/discourse/{site}"},
        )
    response.raise_for_status()  # an empty body, which `bridge.discourse.api` would parse


@pytest.fixture(scope="session")
async def archon():
    base, _, name = os.environ["DATABASE_URL"].rpartition("/")
    async with await psycopg.AsyncConnection.connect(f"{base}/postgres", autocommit=True) as conn:
        if not await (
            await conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,))
        ).fetchone():
            await conn.execute(
                psycopg.sql.SQL("CREATE DATABASE {}").format(psycopg.sql.Identifier(name))
            )
    stand_in = Archon()
    serve(stand_in.app, 8766)
    serve(bridge.app, BRIDGE_PORT)
    # `reach` reads everyone who ever logged in: this session's members only.
    async with await bridge.db() as conn:
        await conn.execute("TRUNCATE usernames")
    sites = bridge.discourse.sites()
    try:
        for site in sites:
            await bridge.discourse.create_role_groups(site)  # as the first sweep after a deploy
            await point_login(site, os.environ["BRIDGE_URL"])
        yield stand_in
    finally:
        # Back to `just dev`'s bridge, whatever a killed run left.
        for site in sites:
            await point_login(site, "http://localhost:8765")


@pytest.fixture
async def browser():
    async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
        yield client


async def login(
    browser: httpx.AsyncClient, site: str, username: str | None = None, lang: str = "en"
):
    """What a member's browser does from the site's login button to landing back on it — on
    `/session/current.json`, which names who the site now sees as logged in."""
    url = os.environ[f"DISCOURSE_{site.upper()}_URL"]
    browser.headers["accept-language"] = lang
    response = await browser.get(
        f"{url}/session/sso", params={"return_path": "/session/current.json"}
    )
    if response.url.path == "/username" and username:
        response = await browser.post(str(response.url), data={"username": username})
    return response


async def discourse_user(site: str, uid: str) -> dict:
    found = await bridge.discourse.by_external_id(site, uid)
    assert found, f"{uid} has no account on {site}"
    return await bridge.discourse.user(site, found["id"])


def sql(site: str, statement: str) -> None:
    """A site's database directly, for a state no API reaches."""
    subprocess.run(
        ["docker", "exec", "-u", "discourse", "vekn-forum-discourse"]
        + ["psql", "-d", f"discourse_{site}", "-v", "ON_ERROR_STOP=1", "-qc", statement],
        check=True,
    )
