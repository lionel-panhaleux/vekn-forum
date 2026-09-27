#!/usr/bin/env bash
# The local stack — wiki/operations.md#local-stack. Idempotent: re-running converges.
set -euo pipefail
cd "$(dirname "$0")/.."

REF=$(cat discourse/ref)
SRC=.local/discourse
NAME=vekn-forum-discourse
SITES="fr intl playtest"
BRIDGE_URL=${BRIDGE_URL:-http://localhost:8765}
ENV_FILE=.local/discourse.env

if [ ! -d "$SRC/.git" ]; then
    git clone --quiet --filter=blob:none --no-checkout https://github.com/discourse/discourse "$SRC"
fi
git -C "$SRC" checkout --quiet "$REF"

{
    for site in $SITES; do
        printf '%s:\n  adapter: postgresql\n  database: discourse_%s\n  prepared_statements: false\n  pool: 5\n  host_names:\n    - %s.localhost\n' "$site" "$site" "$site"
    done
} > "$SRC/config/multisite.yml"

# Per-IP limits off: the bridge and the tests reach every site from one address.
run() {
    docker exec -u discourse:discourse -w /src \
        -e RAILS_ENV=production \
        -e DISCOURSE_HOSTNAME=localhost \
        -e DISCOURSE_SERVE_STATIC_ASSETS=true \
        -e DISCOURSE_MAX_REQS_PER_IP_MODE=none \
        -e DISCOURSE_MAX_ADMIN_API_REQS_PER_MINUTE=6000 \
        -e UNICORN_BIND_ALL=true \
        -e UNICORN_WORKERS=4 \
        "$@"
}

if [ -z "$(docker ps -aq -f name="^$NAME$")" ]; then
    mkdir -p .local/postgres
    docker run -d \
        -p 127.0.0.1:3000:3000 \
        -v "$PWD/.local/postgres:/shared/postgres_data:delegated" \
        -v "$PWD/$SRC:/src:delegated" \
        --hostname=discourse --name="$NAME" \
        discourse/discourse_dev:release /sbin/boot
fi
docker start "$NAME" > /dev/null
if [ -z "$(docker ps -aq -f name="^$NAME-db$")" ]; then
    docker run -d -p 127.0.0.1:5434:5432 -e POSTGRES_USER=bridge -e POSTGRES_PASSWORD=bridge \
        --name="$NAME-db" postgres:17-alpine > /dev/null
fi
docker start "$NAME-db" > /dev/null
until run "$NAME" pg_isready -q; do sleep 1; done

run "$NAME" bundle install --quiet
# The default site (`discourse`) is never visited, but multisite boots through it.
for db in discourse $(printf 'discourse_%s ' $SITES); do
    run "$NAME" sh -c "createdb $db 2>/dev/null || true"
done
run "$NAME" bundle exec rake multisite:migrate > /dev/null

# Assets are built once per Discourse commit: a checkout leaves the previous commit's behind.
STAMP="$SRC/public/assets/.vekn-ref"
if [ "$(cat "$STAMP" 2>/dev/null)" != "$REF" ]; then
    echo "Building Discourse's assets for $REF (minutes, once per commit; log: .local/assets.log)"
    run "$NAME" pnpm install --silent > .local/assets.log 2>&1
    run "$NAME" bundle exec rake assets:precompile >> .local/assets.log 2>&1
    echo "$REF" > "$STAMP"
fi

OLD=$(cat "$ENV_FILE" 2>/dev/null || true)
old() { printf '%s\n' "$OLD" | grep "^DISCOURSE_$1=" | cut -d= -f2- || true; }

: > "$ENV_FILE"
cat >> "$ENV_FILE" <<EOF
DISCOURSE_SITES="$SITES"
DISCOURSE_FR_ADMINS=NC@FR
DISCOURSE_INTL_ADMINS=IC
DISCOURSE_PLAYTEST_ADMINS=PTC
DISCOURSE_PLAYTEST_MEMBERS=PT,PTC
DATABASE_URL=postgresql://bridge:bridge@127.0.0.1:5434/bridge
EOF
docker cp discourse/site.rb "$NAME":/tmp/site.rb
docker exec "$NAME" rm -rf /tmp/vekn-theme /tmp/vekn-sites
docker cp theme "$NAME":/tmp/vekn-theme
docker cp discourse/sites "$NAME":/tmp/vekn-sites
for site in $SITES; do
    upper=$(echo "$site" | tr '[:lower:]' '[:upper:]')
    secret=$(old "${upper}_SECRET")
    key=$(old "${upper}_API_KEY")
    secret=${secret:-$(openssl rand -hex 16)}
    key=${key:-$(openssl rand -hex 32)}
    gated=""
    [ "$site" = playtest ] && gated="-e SITE_GATED=1"
    identity=""
    [ -d "discourse/sites/$site" ] && identity="-e SITE_IDENTITY_DIR=/tmp/vekn-sites/$site"
    run -e RAILS_DB="$site" \
        -e SITE_URL="http://$site.localhost:3000" \
        -e SITE_LOCALE="$([ "$site" = fr ] && echo fr || echo en)" \
        -e SITE_CONNECT_URL="$BRIDGE_URL/discourse/$site" \
        -e SITE_CONNECT_SECRET="$secret" \
        -e SITE_API_KEY="$key" \
        -e SITE_THEME_DIR=/tmp/vekn-theme \
        $gated $identity \
        "$NAME" bundle exec rails runner /tmp/site.rb
    {
        echo "DISCOURSE_${upper}_URL=http://$site.localhost:3000"
        echo "DISCOURSE_${upper}_SECRET=$secret"
        echo "DISCOURSE_${upper}_API_KEY=$key"
    } >> "$ENV_FILE"
done

# No Sidekiq: the bridge and the tests need the web server alone.
if ! curl -sf -o /dev/null -H 'Host: fr.localhost' http://127.0.0.1:3000/srv/status; then
    run -d "$NAME" bundle exec pitchfork -c config/pitchfork.conf.rb
    until curl -sf -o /dev/null -H 'Host: fr.localhost' http://127.0.0.1:3000/srv/status; do sleep 2; done
fi
echo "Discourse up: $(echo $SITES | sed 's/\([a-z]*\)/http:\/\/\1.localhost:3000/g'); env in $ENV_FILE"
