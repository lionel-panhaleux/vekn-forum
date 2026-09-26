"""wiki/engine.md#login, end to end: a site's login button to the member landing back on it."""

import datetime
import os
import secrets

from conftest import discourse_user, login, rails

from bridge import discourse, sweep


def suspended(user: dict) -> bool:
    until = user.get("suspended_till")
    return bool(until) and datetime.datetime.fromisoformat(until) > datetime.datetime.now(
        datetime.UTC
    )


def handle() -> str:
    return f"m{secrets.token_hex(4)}"


async def test_a_first_login_asks_a_username_once_and_creates_the_user(archon, browser):
    uid = archon.member()
    name = handle()
    response = await login(browser, "fr")
    assert response.url.path == "/username"
    response = await browser.post(str(response.url), data={"username": "no spaces"})
    assert response.status_code == 400
    response = await browser.post(str(response.url), data={"username": name})
    assert response.json()["current_user"]["username"] == name
    user = await discourse_user("fr", uid)
    assert user["username"] == name
    email = archon.members[uid]["email"]
    by_email = await discourse.api(
        "fr", "GET", "/admin/users/list/all.json", params={"email": email}
    )
    assert [u["id"] for u in by_email] == [user["id"]]
    # Another site: the same handle, nothing asked.
    response = await login(browser, "intl")
    assert response.json()["current_user"]["username"] == name
    assert (await discourse_user("intl", uid))["username"] == name


async def test_a_legacy_account_with_the_same_email_is_claimed_not_duplicated(archon, browser):
    uid = archon.member()
    old = handle()
    legacy_id = rails(
        "fr",
        f"puts User.create!(username: '{old}', email: '{archon.members[uid]['email']}', "
        "active: true, approved: true).id",
    )
    response = await login(browser, "fr")
    assert response.json()["current_user"]["username"] == old
    user = await discourse_user("fr", uid)
    assert str(user["id"]) == legacy_id.splitlines()[-1]
    assert user["username"] == old


async def test_an_nc_is_admin_on_their_own_site_only(archon, browser):
    uid = archon.member(roles=["NC"], country="FR")
    await login(browser, "fr", handle())
    await login(browser, "intl")
    fr, intl = await discourse_user("fr", uid), await discourse_user("intl", uid)
    assert fr["admin"] and not intl["admin"]
    assert "nc" in {g["name"] for g in fr["groups"]} and "nc" in {g["name"] for g in intl["groups"]}


async def test_a_revoked_nc_loses_admin_without_logging_in(archon, browser):
    uid = archon.member(roles=["NC"], country="FR")
    await login(browser, "fr", handle())
    assert (await discourse_user("fr", uid))["admin"]
    archon.members[uid]["roles"] = []
    await sweep.sweep()
    user = await discourse_user("fr", uid)
    assert not user["admin"] and "nc" not in {g["name"] for g in user["groups"]}


async def test_a_member_without_a_verified_email_is_sent_to_archon(archon, browser):
    archon.member(email=None)
    response = await login(browser, "fr")
    assert response.status_code == 403
    assert f'href="{os.environ["ARCHON_URL"]}/profile"' in response.text


async def test_a_forged_login_request_is_refused(archon, browser):
    response = await browser.get(
        "http://localhost:8765/discourse/fr", params={"sso": "bm9uY2U9MQ==", "sig": "0" * 64}
    )
    assert response.status_code == 403


async def test_the_playtest_site_admits_pt_and_ptc_only_and_suspends_on_loss(archon, browser):
    archon.member(roles=["Judge"])
    response = await login(browser, "playtest", handle())
    assert response.status_code == 403
    uid = archon.member(roles=["PT"])
    response = await login(browser, "playtest", handle())
    assert response.json()["current_user"]
    # A moderator's past suspension, long expired, must not read as one.
    user_id = (await discourse_user("playtest", uid))["id"]
    rails(
        "playtest",
        f"User.find({user_id}).update!(suspended_at: 3.days.ago, suspended_till: 1.day.ago)",
    )
    archon.members[uid]["roles"] = []
    await sweep.sweep()
    assert suspended(await discourse_user("playtest", uid))
    archon.members[uid]["roles"] = ["PTC"]
    await sweep.sweep()
    user = await discourse_user("playtest", uid)
    assert not suspended(user) and user["admin"]


async def test_a_lost_role_removes_its_language_groups(archon, browser):
    group = f"judge-{secrets.token_hex(3)}"
    rails("intl", f"Group.create!(name: '{group}')")
    uid = archon.member(roles=["Judge"])
    await login(browser, "intl", handle())
    user_id = (await discourse_user("intl", uid))["id"]
    rails("intl", f"Group.find_by(name: '{group}').add(User.find({user_id}))")
    archon.members[uid]["roles"] = ["Rulemonger"]
    await sweep.sweep()
    assert group in {g["name"] for g in (await discourse_user("intl", uid))["groups"]}
    archon.members[uid]["roles"] = []
    await sweep.sweep()
    assert group not in {g["name"] for g in (await discourse_user("intl", uid))["groups"]}
