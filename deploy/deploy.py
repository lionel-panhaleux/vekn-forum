import hashlib
import socket
import subprocess
import tempfile
from io import StringIO
from pathlib import Path

import jinja2
from pyinfra import host
from pyinfra.facts.server import Command
from pyinfra.operations import apt, files, server, systemd
from pyinfra.operations.util import any_changed
from server_setup import nginx_site, postgres_db
from server_setup.secrets import load, put_secret

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
BASE = "forum.krcg.org"
# The launcher's own site (db `default`) is intl; every other site is a multisite.yml entry.
SITES = {
    "intl": {"db": "default", "locale": "en", "admins": "IC"},
    "fr": {"db": "fr", "locale": "fr", "admins": "NC@FR"},
}
DEFAULT = "intl"
REF = (REPO / "discourse/ref").read_text().strip()
LAUNCHER_REF = "8d705a91866c320592ce851f30895ddb4c3e85fe"  # discourse/discourse_docker
DISCOURSE = "/var/discourse"
# one directory per container: `data` holds Postgres and Redis, `app` the uploads and backups
DATA = f"{DISCOURSE}/shared/data"
WEB = f"{DISCOURSE}/shared/web-only"
MAIL = "codex.of.the.damned@gmail.com"
DEVELOPER_EMAILS = "lionel.panhaleux@gmail.com"
NAME = "vekn_forum"
UNIT = "vekn-forum"
OPT = f"/opt/{NAME}"
ETC = f"/etc/{NAME}"
BRIDGE_PORT = 8030
BRIDGE_URL = f"https://{BASE}"
ARCHON_URL, ARCHON_API_URL = "https://archon.krcg.org", "https://api.archon.krcg.org"  # beta
BACKUP_REPO = f"{NAME}_discourse"
UV = "/usr/local/bin/uv"


def domain(site: str) -> str:
    return f"{site}.{BASE}"


# A certificate request for a name that does not resolve here fails, and Let's Encrypt counts
# every failed validation against its hourly limit.
for name in [BASE, *map(domain, SITES)]:
    try:
        ip = socket.gethostbyname(name)
    except socket.gaierror:
        ip = None
    if ip != host.data.ssh_hostname:
        raise RuntimeError(f"{name} resolves to {ip}, not {host.data.ssh_hostname}")

secrets = load(str(HERE / "secrets.sops.yaml"))
if not {"archon_client_id", "archon_client_secret"} <= secrets.keys():
    raise RuntimeError(
        "no archon client in `just secrets` yet: register it first (wiki/operations.md#deploy)"
    )


def render(template: str, **values) -> str:
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(HERE / "files"),
        trim_blocks=True,
        keep_trailing_newline=True,
        undefined=jinja2.StrictUndefined,
    )
    return env.get_template(template).render(**values)


def env_file(values: dict) -> str:
    for key, value in values.items():
        if "'" in str(value) or "\n" in str(value):
            raise ValueError(f"{key} holds a quote or a newline, which the env file cannot carry")
    return "".join(f"{key}='{value}'\n" for key, value in values.items())


def digest(*parts: bytes) -> str:
    return hashlib.sha256(b"\0".join(parts)).hexdigest()[:16]


def marker(path: str) -> str:
    return host.get_fact(Command, f"cat {path} 2>/dev/null || true") or ""


postgres_units = (
    host.get_fact(
        Command,
        "systemctl list-units --plain --no-legend --state=active 'postgresql@*.service' | awk '{print $1}'",
    )
    or ""
).split()
if len(postgres_units) != 1:
    raise RuntimeError(f"expected one running PostgreSQL cluster, found {postgres_units}")
postgres_unit = postgres_units[0]


server.group(name="Bridge group", group=NAME, system=True)
server.user(
    name="Bridge user",
    user=NAME,
    group=NAME,
    home=OPT,
    shell="/usr/sbin/nologin",
    system=True,
    create_home=False,
    ensure_home=False,
)
files.directory(name="Config dir", path=ETC, user="root", group=NAME, mode="750")

# --- Discourse: the official launcher, a database container and a web container for every site

apt.packages(name="Docker", packages=["docker.io"], update=True, cache_time=3600)
systemd.service(name="Docker running", service="docker", running=True, enabled=True)

launcher = []
if marker(f"{DISCOURSE}/.git/HEAD") != LAUNCHER_REF:
    launcher.append(
        server.shell(
            name="Discourse launcher",
            commands=[
                f"test -d {DISCOURSE}/.git || git clone https://github.com/discourse/discourse_docker {DISCOURSE}",
                f"git -C {DISCOURSE} fetch origin",
                # detached: `launcher rebuild` updates itself only on the main branch
                f"git -C {DISCOURSE} checkout --quiet {LAUNCHER_REF}",
            ],
        )
    )
files.directory(name="Launcher containers", path=f"{DISCOURSE}/containers", mode="700")
extra_sites = [
    {"db": s["db"], "domain": domain(site)} for site, s in SITES.items() if site != DEFAULT
]
data_yml = put_secret(
    "Discourse data.yml",
    render(
        "data.yml.j2",
        data_dir=DATA,
        db_password=secrets["discourse_db_password"],
        extra_sites=extra_sites,
    ),
    f"{DISCOURSE}/containers/data.yml",
)
app_yml = put_secret(
    "Discourse app.yml",
    render(
        "app.yml.j2",
        ref=REF,
        web_dir=WEB,
        host_ip=host.data.ssh_hostname,
        default_domain=domain(DEFAULT),
        developer_emails=DEVELOPER_EMAILS,
        db_password=secrets["discourse_db_password"],
        mail=MAIL,
        mail_password=secrets["mail_password"],
        extra_sites=extra_sites,
    ),
    f"{DISCOURSE}/containers/app.yml",
)


def container_running(name: str) -> bool:
    return (
        host.get_fact(
            Command, f"docker inspect -f '{{{{.State.Running}}}}' {name} 2>/dev/null || true"
        )
        == "true"
    )


data_running, app_running = container_running("data"), container_running("app")
data = server.shell(
    name="Rebuild Discourse's database (every site down meanwhile)",
    commands=[f"cd {DISCOURSE} && ./launcher rebuild data"],
    _if=lambda: not data_running or any_changed(data_yml, *launcher)(),
)
# `bootstrap` builds the new image while the running container serves; only the swap is downtime.
swap = server.shell(
    name="Build Discourse, then swap it in",
    commands=[
        f"cd {DISCOURSE} && ./launcher bootstrap app",
        f"cd {DISCOURSE} && if docker inspect app > /dev/null 2>&1; then ./launcher destroy app; fi",
        f"cd {DISCOURSE} && ./launcher start app",
        "docker image prune -f",
    ],
    _if=lambda: not app_running or any_changed(app_yml, *launcher)(),
)
# the containers' link resolves the database's address when `app` starts
server.shell(
    name="Restart Discourse on its rebuilt database",
    commands=[f"cd {DISCOURSE} && ./launcher restart app"],
    _if=lambda: data.did_change() and not swap.did_change(),
)

# --- Sites: settings, the base theme, the site's identity and the bridge's API key, from site.rb


def tree(path: Path) -> list[bytes]:
    return [
        bytes(f.relative_to(path)) + b"\0" + f.read_bytes()
        for f in sorted(path.rglob("*"))
        if f.is_file()
    ]


site_rb = (REPO / "discourse/site.rb").read_bytes()
files.put(
    name="Site settings script",
    src=str(REPO / "discourse/site.rb"),
    dest=f"{WEB}/vekn-forum-site.rb",
)
files.sync(name="Base theme", src=str(REPO / "theme"), dest=f"{WEB}/vekn-forum-theme", delete=True)
files.sync(
    name="Site identities",
    src=str(REPO / "discourse/sites"),
    dest=f"{WEB}/vekn-forum-sites",
    delete=True,
)
theme = tree(REPO / "theme")
provisioned = []
for site, s in SITES.items():
    env = {
        "RAILS_DB": s["db"],
        "SITE_URL": f"https://{domain(site)}",
        "SITE_LOCALE": s["locale"],
        "SITE_CONNECT_URL": f"{BRIDGE_URL}/discourse/{site}",
        "SITE_CONNECT_SECRET": secrets[f"{site}_connect_secret"],
        "SITE_API_KEY": secrets[f"{site}_api_key"],
        "SITE_EMAIL": MAIL,
        "SITE_THEME_DIR": "/shared/vekn-forum-theme",
    }
    identity = REPO / "discourse/sites" / site
    if identity.is_dir():
        env["SITE_IDENTITY_DIR"] = f"/shared/vekn-forum-sites/{site}"
    # docker's --env-file takes quotes literally
    content = "".join(f"{key}={value}\n" for key, value in env.items())
    site_env = f"{ETC}/site-{site}.env"
    put_secret(f"{site} site env", content, site_env)
    # A marker, not the upload's did_change: a run that uploaded then failed must not look finished.
    # It lives beside the database it describes, and goes with it.
    expected = digest(site_rb, content.encode(), *theme, *tree(identity))
    done = f"{DATA}/vekn-forum-site-{site}.provisioned"
    if marker(done) != expected:
        provisioned.append(
            server.shell(
                name=f"Provision {site}",
                commands=[
                    (
                        f"docker exec --env-file {site_env} -u discourse -w /var/www/discourse app "
                        "bundle exec rails runner /shared/vekn-forum-site.rb"
                    ),
                    f"echo {expected} > {done}",
                ],
            )
        )
    nginx_site(
        site=f"{NAME}_{site}",
        domain=domain(site),
        type="proxy",
        upstream=f"http://unix:{WEB}/nginx.http.sock:",
    )

# --- Backups: each site's own daily archive, pushed to the fleet's restic bucket

files.put(
    name="Discourse backup script",
    src=str(HERE / "files/discourse-backup.sh"),
    dest=f"/usr/local/bin/{UNIT}-discourse-backup",
    mode="755",
)
# the host's nightly orphan scan skips a repo declared here (server-setup OPERATIONS.md)
files.file(name="Declare the backup repo", path=f"/etc/postgres-backup/repos.d/{BACKUP_REPO}")
backup_units = [
    files.put(
        name="Discourse backup unit",
        src=StringIO(render("discourse-backup.service.j2", repo=BACKUP_REPO, unit=UNIT)),
        dest=f"/etc/systemd/system/{UNIT}-discourse-backup.service",
        mode="644",
    ),
    files.put(
        name="Discourse backup timer",
        src=str(HERE / "files/discourse-backup.timer"),
        dest=f"/etc/systemd/system/{UNIT}-discourse-backup.timer",
        mode="644",
    ),
]
systemd.daemon_reload(name="Reload units for backups", _if=any_changed(*backup_units))
systemd.service(
    name="Discourse backup timer",
    service=f"{UNIT}-discourse-backup.timer",
    running=True,
    enabled=True,
)

# --- Bridge: the login service and its sweep

files.directory(name="Bridge root", path=OPT, user=NAME, group=NAME, mode="755")
postgres_db(database=NAME, owner=NAME)

# Ship the built wheel, never the source tree: only what the package declares reaches the server.
dist = Path(tempfile.mkdtemp())
subprocess.run(["uv", "build", "--wheel", "--quiet", "--out-dir", dist], cwd=REPO, check=True)
(wheel,) = dist.glob("*.whl")
requirements = subprocess.run(
    ["uv", "export", "--frozen", "--no-dev", "--no-emit-project", "--no-header", "--no-annotate"],
    cwd=REPO,
    check=True,
    capture_output=True,
    text=True,
).stdout
expected = digest(requirements.encode(), wheel.read_bytes())
# A wheel is binary and pyinfra diffs any file it replaces: each build lands in a new directory instead.
installed = f"dist/{expected}/{wheel.name}"
code = [
    files.put(
        name="Upload requirements",
        src=StringIO(requirements),
        dest=f"{OPT}/requirements.txt",
        user=NAME,
        group=NAME,
    ),
    files.put(
        name="Upload wheel",
        src=str(wheel),
        dest=f"{OPT}/{installed}",
        user=NAME,
        group=NAME,
    ),
]
if marker(f"{OPT}/.venv/.deployed") != expected:
    code.append(
        server.shell(
            name="Install the bridge",
            commands=[
                f"test -d .venv || {UV} venv --python /usr/bin/python3 .venv",
                f"{UV} pip sync --no-cache requirements.txt",
                f"{UV} pip install --no-cache --no-deps --reinstall {installed}",
                f"echo {expected} > .venv/.deployed",
            ],
            _sudo_user=NAME,
            _env={"UV_PYTHON_DOWNLOADS": "never"},
            # uv reads uv.toml from the working directory: the SSH user's home is off limits
            _chdir=OPT,
        )
    )
    server.shell(
        name="Drop older wheels",
        commands=[
            f"find {OPT}/dist -mindepth 1 -maxdepth 1 ! -name {expected} -exec rm -rf {{}} +"
        ],
    )

bridge_env = {
    "BRIDGE_URL": BRIDGE_URL,
    "BRIDGE_SECRET": secrets["bridge_secret"],
    "DATABASE_URL": f"postgresql:///{NAME}?host=/var/run/postgresql",
    "ARCHON_URL": ARCHON_URL,
    "ARCHON_API_URL": ARCHON_API_URL,
    "ARCHON_CLIENT_ID": secrets["archon_client_id"],
    "ARCHON_CLIENT_SECRET": secrets["archon_client_secret"],
    "DISCOURSE_SITES": " ".join(SITES),
}
for site, s in SITES.items():
    upper = site.upper()
    bridge_env |= {
        f"DISCOURSE_{upper}_URL": f"https://{domain(site)}",
        f"DISCOURSE_{upper}_SECRET": secrets[f"{site}_connect_secret"],
        f"DISCOURSE_{upper}_API_KEY": secrets[f"{site}_api_key"],
        f"DISCOURSE_{upper}_ADMINS": s["admins"],
    }
code.append(
    put_secret("Bridge env", env_file(bridge_env), f"{ETC}/bridge.env", group=NAME, mode="640")
)

units = {"bridge": f"{UNIT}-bridge.service", "sweep": f"{UNIT}-sweep.service"}
values = {"name": NAME, "opt": OPT, "etc": ETC, "port": BRIDGE_PORT, "postgres_unit": postgres_unit}
unit_files = [
    files.put(
        name=f"Install {unit}",
        src=StringIO(render(f"{kind}.service.j2", **values)),
        dest=f"/etc/systemd/system/{unit}",
        mode="644",
    )
    for kind, unit in units.items()
]
unit_files.append(
    files.put(
        name="Install sweep timer",
        src=str(HERE / "files/sweep.timer"),
        dest=f"/etc/systemd/system/{UNIT}-sweep.timer",
        mode="644",
    )
)
systemd.daemon_reload(name="Reload units for the bridge", _if=any_changed(*unit_files))
systemd.service(name="Bridge running", service=units["bridge"], running=True, enabled=True)
systemd.service(
    name="Restart the bridge",
    service=units["bridge"],
    restarted=True,
    _if=any_changed(*unit_files, *code),
)
systemd.service(name="Sweep timer", service=f"{UNIT}-sweep.timer", running=True, enabled=True)
nginx_site(site=NAME, domain=BASE, type="proxy", upstream=f"http://127.0.0.1:{BRIDGE_PORT}")

# The sweep creates the role groups a login's payload names: run it once a site is (re)provisioned,
# and again until it has succeeded.
swept = host.get_fact(Command, f"systemctl show -p Result --value {units['sweep']}") == "success"
server.shell(
    name="Sweep now",
    commands=[f"systemctl start {units['sweep']}"],
    _if=lambda: not swept or any_changed(data, swap, *provisioned)(),
)
