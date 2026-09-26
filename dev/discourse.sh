#!/usr/bin/env bash
# Local Discourse multisite (fr, intl, playtest) and the bridge's Postgres, for the bridge tests — see wiki/operations.md.
# Idempotent: re-running converges. Writes the bridge's per-site env to .local/discourse.env.
set -euo pipefail
cd "$(dirname "$0")/.."

REF=bf55a44c2872738f7ae2664d6fec3d6d8779190f
SRC=.local/discourse
NAME=vekn-forum-discourse
SITES="fr intl playtest"
BRIDGE_URL=${BRIDGE_URL:-http://localhost:8765}
ROLE_GROUPS="ic nc prince ethics ptc pt rulemonger judge sheriff dev"
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

run() { docker exec -u discourse:discourse -w /src "$@"; }

if [ -z "$(docker ps -aq -f name="^$NAME$")" ]; then
    mkdir -p .local/postgres
    docker run -d \
        -p 127.0.0.1:3000:3000 \
        -v "$PWD/.local/postgres:/shared/postgres_data:delegated" \
        -v "$PWD/$SRC:/src:delegated" \
        -e UNICORN_BIND_ALL=true \
        -e DISCOURSE_MAX_ADMIN_API_REQS_PER_MINUTE=6000 \
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
run "$NAME" pnpm install --silent
run "$NAME" bundle exec rake db:create db:migrate > /dev/null

: > "$ENV_FILE"
cat >> "$ENV_FILE" <<EOF
DISCOURSE_SITES="$SITES"
DISCOURSE_FR_ADMINS=NC@FR
DISCOURSE_INTL_ADMINS=IC
DISCOURSE_PLAYTEST_ADMINS=PTC
DISCOURSE_PLAYTEST_MEMBERS=PT,PTC
DATABASE_URL=postgresql://bridge:bridge@127.0.0.1:5434/bridge
EOF
for site in $SITES; do
    run "$NAME" sh -c "createdb discourse_$site 2>/dev/null || true" 
    run -e RAILS_DB="$site" "$NAME" bundle exec rake db:migrate > /dev/null
    secret=$(openssl rand -hex 16)
    # Group names are validated as usernames: 3 characters minimum by default, and `ic`, `nc`,
    # `pt` are two.
    key=$(run -e RAILS_DB="$site" "$NAME" bundle exec rails runner "
        SiteSetting.min_username_length = 2
        SiteSetting.discourse_connect_url = '$BRIDGE_URL/discourse/$site'
        SiteSetting.discourse_connect_secret = '$secret'
        SiteSetting.enable_discourse_connect = true
        SiteSetting.email_editable = false
        SiteSetting.auth_overrides_email = true
        if '$site' == 'playtest'
          SiteSetting.login_required = true
          SiteSetting.allow_index_in_robots_txt = false
        end
        '$ROLE_GROUPS'.split.each { |g| Group.find_or_create_by!(name: g) }
        ApiKey.where(description: 'bridge').destroy_all
        puts ApiKey.create!(description: 'bridge', created_by_id: Discourse::SYSTEM_USER_ID).key
    " | tail -1)
    upper=$(echo "$site" | tr '[:lower:]' '[:upper:]')
    {
        echo "DISCOURSE_${upper}_URL=http://$site.localhost:3000"
        echo "DISCOURSE_${upper}_SECRET=$secret"
        echo "DISCOURSE_${upper}_API_KEY=$key"
    } >> "$ENV_FILE"
done

# The bridge only needs Rails: no Ember build, no Sidekiq.
if ! curl -sf -o /dev/null -H 'Host: fr.localhost' http://127.0.0.1:3000/srv/status; then
    run -d "$NAME" bundle exec rails server -b 0.0.0.0 -p 3000
    until curl -sf -o /dev/null -H 'Host: fr.localhost' http://127.0.0.1:3000/srv/status; do sleep 2; done
fi
echo "Discourse up: $(echo $SITES | sed 's/\([a-z]*\)/http:\/\/\1.localhost:3000/g'); env in $ENV_FILE"
