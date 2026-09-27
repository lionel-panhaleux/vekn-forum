"""The bridge between the real local Discourse sites (`just discourse`) and a stand-in archon.

The stand-in speaks archon's documented contract (wiki/archon.md) over HTTP — consent, PKCE token
exchange, userinfo, `client_credentials`, `/v1/users/{uid}` with `sanctions` for the daemon token
alone — and nothing of the bridge's
internals. archon itself is proven after deploy (wiki/post-deploy.md).
"""

import asyncio
import base64
import hashlib
import json
import os
import pathlib
import re
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
    raise RuntimeError("no local Discourse: run `just discourse` first")
for line in ENV.read_text().splitlines():
    key, _, value = line.partition("=")
    os.environ[key] = value.strip('"')
ARCHON = f"http://127.0.0.1:{8766}"
# Beside `just bridge` (8765, database `bridge`), so a test run disturbs neither its port nor its
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
import bridge.sweep


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


def connect_url(site: str, value: str) -> str:
    """Point the site's login button (`discourse_connect_url`) at `value`; the previous one."""
    url = os.environ[f"DISCOURSE_{site.upper()}_URL"] + "/admin/site_settings"
    headers = {"Api-Key": os.environ[f"DISCOURSE_{site.upper()}_API_KEY"], "Api-Username": "system"}
    settings = httpx.get(f"{url}.json", headers=headers, params={"filter": "discourse_connect_url"})
    [previous] = [
        s["value"]
        for s in settings.raise_for_status().json()["site_settings"]
        if s["setting"] == "discourse_connect_url"
    ]
    data = {"discourse_connect_url": value}
    httpx.put(f"{url}/discourse_connect_url", headers=headers, data=data).raise_for_status()
    return previous


async def forget(site: str, user: dict) -> None:
    """Delete a member a previous session created; Discourse deletes no admin or moderator."""
    api = bridge.discourse.api
    for right, revoke in (("admin", "revoke_admin"), ("moderator", "revoke_moderation")):
        if user.get(right):
            await api(site, "PUT", f"/admin/users/{user['id']}/{revoke}")
    await api(site, "DELETE", f"/admin/users/{user['id']}.json", params={"delete_posts": "true"})


async def reset() -> None:
    """Forget the members and language groups tests made: the sweep reads every user of a gated
    site, everyone who ever logged in and every language group, so leftovers slow every sweep."""
    api = bridge.discourse.api
    async with await bridge.db() as conn:
        await conn.execute("TRUNCATE usernames")
    for site in bridge.discourse.sites():
        seen: set[int] = set()
        while left := await api(
            site, "GET", "/admin/users/list/all.json", params={"filter": "@example.com"}
        ):
            ids = {u["id"] for u in left}
            assert not ids & seen, f"{site}: users {ids & seen} survived their deletion"
            seen |= ids
            await asyncio.gather(*(forget(site, u) for u in left))
        found = await api(site, "GET", "/groups.json", params={"filter": "judge-"})
        await asyncio.gather(
            *(
                api(site, "DELETE", f"/admin/groups/{g['id']}.json")
                for g in found["groups"]
                if re.fullmatch(r"judge-[0-9a-f]{6}", g["name"])
            )
        )


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
    await reset()
    bridge.sweep.PACE = 0.0  # archon's lookup budget; the stand-in has none
    await bridge.sweep.sweep()  # as after a deploy: creates the role groups
    sites = bridge.discourse.sites()
    dev = {
        site: connect_url(site, f"{os.environ['BRIDGE_URL']}/discourse/{site}") for site in sites
    }
    yield stand_in
    for site, url in dev.items():
        connect_url(site, url)


@pytest.fixture
async def browser():
    async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
        yield client
    await reset()


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


# Rails boots in ~10 s: one runner for the whole session, started at import so it boots while the
# session sets up, evaluating each snippet on the named site's database.
RUNNER = subprocess.Popen(
    ["docker", "exec", "-i", "-u", "discourse", "-w", "/src", "vekn-forum-discourse"]
    + [
        "bundle",
        "exec",
        "rails",
        "runner",
        """
STDOUT.sync = true
STDIN.each_line do |line|
  site, code = JSON.parse(line)
  out = StringIO.new
  $stdout = out
  error = begin
    RailsMultisite::ConnectionManagement.with_connection(site) { eval(code) }
    nil
  rescue Exception => e
    "#{e.class}: #{e.message}"
  ensure
    $stdout = STDOUT
  end
  STDOUT.puts({out: out.string, error: error}.to_json)
end
""",
    ],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True,
)


def rails(site: str, code: str) -> str:
    """Server-side Discourse, as the phpBB importer would act on it."""
    assert RUNNER.stdin and RUNNER.stdout
    RUNNER.stdin.write(json.dumps([site, code]) + "\n")
    RUNNER.stdin.flush()
    while not (line := RUNNER.stdout.readline()).startswith('{"out":'):
        assert line, "the Rails runner exited"
    reply = json.loads(line)
    assert not reply["error"], reply["error"]
    return reply["out"].strip()
