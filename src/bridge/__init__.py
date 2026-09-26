"""The archon login bridge: a DiscourseConnect provider for every site — wiki/engine.md#login."""

import contextlib
import html
import os
import re
import secrets
import urllib.parse

import psycopg
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from . import archon, discourse

USERNAME = re.compile(r"[\w.-]{2,20}")


async def db() -> psycopg.AsyncConnection:
    return await psycopg.AsyncConnection.connect(os.environ["DATABASE_URL"], autocommit=True)


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    async with await db() as conn:
        await conn.execute(
            "CREATE TABLE IF NOT EXISTS usernames (archon_uid TEXT PRIMARY KEY, username TEXT NOT NULL)"
        )
    yield


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ["BRIDGE_SECRET"],
    session_cookie="bridge",
    max_age=3600,
    https_only=os.environ["BRIDGE_URL"].startswith("https://"),
)


@app.get("/discourse/{site}")
async def login(request: Request, site: str, sso: str, sig: str):
    """Discourse sends the member here; archon's consent screen is the only step in between."""
    if site not in discourse.sites():
        raise HTTPException(404)
    try:
        payload = discourse.decode(site, sso, sig)
    except ValueError:
        raise HTTPException(403) from None
    if not payload.get("return_sso_url", "").startswith(discourse.env(site, "URL") + "/"):
        raise HTTPException(403)
    state, verifier = secrets.token_urlsafe(24), secrets.token_urlsafe(48)
    request.session.clear()
    request.session["login"] = {
        "site": site,
        "nonce": payload["nonce"],
        "return": payload["return_sso_url"],
        "state": state,
        "verifier": verifier,
    }
    return RedirectResponse(archon.authorization_url(state, verifier), 302)


@app.get("/callback")
async def callback(request: Request, state: str = "", code: str = ""):
    login = request.session.get("login")
    if not login or not code or not secrets.compare_digest(state, login["state"]):
        return page("Login expired", "<p>Go back to the forum and log in again.</p>", 400)
    try:
        token = await archon.exchange_code(code, login["verifier"])
        info = await archon.userinfo(token)
        member = await archon.member(info["sub"], token)
    except archon.Error:
        return page("archon is unreachable", "<p>Try again in a moment.</p>", 502)
    if not info.get("email"):
        profile = html.escape(archon.app_url() + "/profile")
        return page(
            "Add an email in archon",
            "<p>The forum links your account by the email archon has verified, and archon has "
            f'none for you yet.</p><p><a class="button" href="{profile}">Open archon</a></p>',
            403,
        )
    if not discourse.admitted(login["site"], info["roles"]):
        return page("Playtesters only", "<p>This forum is open to archon's PT and PTC.</p>", 403)
    login |= {
        "uid": info["sub"],
        "email": info["email"],
        "roles": info["roles"],
        "country": member.get("country"),
    }
    request.session["login"] = login
    async with await db() as conn:
        row = await (
            await conn.execute(
                "SELECT username FROM usernames WHERE archon_uid = %s", (login["uid"],)
            )
        ).fetchone()
        username = row[0] if row else None
        if not username:
            username = await discourse.username_for_email(login["site"], login["email"])
            if username:
                await remember(conn, login["uid"], username)
    if not username:
        return RedirectResponse("/username", 303)
    return await finish(request, username)


@app.get("/username")
async def ask_username(request: Request):
    if "uid" not in request.session.get("login", {}):
        return page("Login expired", "<p>Go back to the forum and log in again.</p>", 400)
    return username_form()


@app.post("/username")
async def set_username(request: Request, username: str = Form()):
    login = request.session.get("login", {})
    if "uid" not in login:
        return page("Login expired", "<p>Go back to the forum and log in again.</p>", 400)
    username = username.strip()
    if not USERNAME.fullmatch(username):
        return username_form(username, "2 to 20 letters, digits, dots, dashes or underscores.")
    async with await db() as conn:
        await remember(conn, login["uid"], username)
    return await finish(request, username)


async def remember(conn: psycopg.AsyncConnection, uid: str, username: str) -> None:
    await conn.execute(
        "INSERT INTO usernames VALUES (%s, %s) ON CONFLICT (archon_uid) DO NOTHING", (uid, username)
    )


async def finish(request: Request, username: str) -> RedirectResponse:
    """Sign the site its payload. `require_activation` is never sent: without it Discourse links
    the login to an existing account with the same email — the legacy claim (wiki/engine.md)."""
    login = request.session.pop("login")
    site = login["site"]
    fields = await discourse.rights(site, login["uid"], login["roles"], login["country"])
    fields |= {"nonce": login["nonce"], "email": login["email"], "username": username}
    if discourse.gate(site) and (existing := await discourse.by_external_id(site, login["uid"])):
        await discourse.admit(site, await discourse.user(site, existing["id"]), login["roles"])
    query = urllib.parse.urlencode(discourse.encode(site, fields))
    return RedirectResponse(f"{login['return']}?{query}", 302)


def username_form(value: str = "", error: str = "") -> HTMLResponse:
    return page(
        "Choose your username",
        '<form method="post"><label for="u">Shown on your posts, on every VEKN forum.</label>'
        f'<input id="u" name="username" value="{html.escape(value)}" required autofocus '
        'autocomplete="username" autocapitalize="none" spellcheck="false">'
        + (f'<p class="error">{html.escape(error)}</p>' if error else "")
        + '<button class="button">Continue</button></form>',
        400 if error else 200,
    )


def page(title: str, body: str, status: int = 200) -> HTMLResponse:
    return HTMLResponse(
        f"""<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>
:root{{color-scheme:light dark;font:16px/1.5 system-ui,sans-serif}}
body{{margin:0 auto;max-width:28rem;padding:2rem 1rem}}
h1{{font-size:1.4rem}}
label{{display:block;margin-bottom:.5rem}}
input{{box-sizing:border-box;width:100%;min-height:44px;font:inherit;padding:0 .75rem}}
.button{{display:inline-block;box-sizing:border-box;width:100%;min-height:44px;margin-top:1rem;
font:inherit;text-align:center;line-height:44px;border:0;border-radius:6px;
background:#8b0000;color:#fff;text-decoration:none}}
.error{{color:#c00}}
</style>
<h1>{html.escape(title)}</h1>{body}</html>""",
        status,
    )
