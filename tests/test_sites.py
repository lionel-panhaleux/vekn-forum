"""Site provisioning (discourse/site.rb): the base theme and each site's tokens, wiki/design.md#theming."""

import json
import os
import pathlib
import re

import httpx

REPO = pathlib.Path(__file__).parent.parent
DESIGN = (REPO / "wiki/design.md").read_text()


def palettes(site: str) -> list[dict[str, str]]:
    info = httpx.get(f"{os.environ[f'DISCOURSE_{site.upper()}_URL']}/site.json").json()
    assert [(t["name"], t["default"]) for t in info["user_themes"]] == [("VEKN", True)]
    return [
        {c["name"]: c["hex"].upper() for c in info[f"default_{mode}_color_scheme"]["colors"]}
        for mode in ("light", "dark")
    ]


def test_a_site_with_an_identity_wears_its_tokens():
    identity = json.loads((REPO / "discourse/sites/fr/identity.json").read_text())
    light, dark = palettes("fr")
    assert light == identity["palettes"]["light"]
    assert dark == identity["palettes"]["dark"]
    basic = httpx.get(f"{os.environ['DISCOURSE_FR_URL']}/site/basic-info.json").json()
    assert basic["title"] == identity["title"]
    assert basic["logo_url"] and basic["logo_small_url"]


def test_a_site_without_one_wears_the_base_palettes():
    schemes = json.loads((REPO / "theme/about.json").read_text())["color_schemes"]
    light, dark = palettes("intl")
    assert light.items() >= schemes["VEKN"].items()
    assert dark.items() >= schemes["VEKN Dark"].items()


def test_every_site_serves_the_base_theme_icons():
    names = re.findall(r'<symbol id="([^"]+)"', (REPO / "theme/assets/icons.svg").read_text())
    assert sorted(names) == sorted(
        re.findall(r"^\| [^|]+ \| `(vekn-[a-z]+)` \|", DESIGN, re.MULTILINE)
    )
    for site in ("fr", "intl"):
        url = os.environ[f"DISCOURSE_{site.upper()}_URL"]
        host = httpx.URL(url).host
        for name in names:
            assert httpx.get(f"{url}/svg-sprite/{host}/icon/{name}.svg").status_code == 200, name


def test_no_site_lists_discourse_stock_categories():
    for site in ("fr", "intl"):
        url = os.environ[f"DISCOURSE_{site.upper()}_URL"]
        listed = httpx.get(f"{url}/categories.json").json()["category_list"]["categories"]
        assert {"general", "site-feedback", "uncategorized"}.isdisjoint(c["slug"] for c in listed)
