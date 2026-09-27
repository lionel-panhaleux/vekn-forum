#!/usr/bin/env bash
# vekn.fr's phpBB dump into a Discourse's fr site — wiki/operations.md#phpbb-import. Runs where the
# Discourse container runs: the local stack by default, or production's `app` container with its root.
# Re-running with a fresher dump tops up: the importer skips what it has already imported.
set -euo pipefail
DUMP=$(realpath "${1:?usage: run.sh <phpbb dump.sql> [container] [discourse root]}")
cd "$(dirname "$0")"
NAME=${2:-vekn-forum-discourse}
ROOT=${3:-/src}
DB=vekn-phpbb

# A fresh copy of the dump for each run, dropped on exit (wiki/operations.md#phpbb-import).
docker rm -f "$DB" > /dev/null 2>&1 || true
docker network create vekn-import > /dev/null 2>&1 || true
# Leaving the container on the network would keep it from starting once the network is gone.
trap 'docker rm -f "$DB" > /dev/null; docker network disconnect vekn-import "$NAME"; docker network rm vekn-import > /dev/null' EXIT
docker run -d --name "$DB" --network vekn-import -e MARIADB_ROOT_PASSWORD=phpbb \
    -e MARIADB_DATABASE=phpbb mariadb:10.11 --max_allowed_packet=256M > /dev/null
docker network connect vekn-import "$NAME" 2> /dev/null || true
until docker exec "$DB" mariadb -uroot -pphpbb -e 'select 1' > /dev/null 2>&1; do sleep 1; done
# Only phpBB 3's tables: the dump also carries phpBB 2's and a card database.
awk '/^-- Table structure for table `/ { keep = ($0 ~ /`phpbb3_/) } /^\/\*!40103 SET TIME_ZONE=@OLD/ { keep = 0 } NR < 20 || keep' "$DUMP" |
    docker exec -i "$DB" mariadb -uroot -pphpbb phpbb

docker exec "$NAME" sh -c 'dpkg -s libmariadb-dev > /dev/null 2>&1 || (apt-get update -qq && apt-get install -y -qq libmariadb-dev > /dev/null)'
docker exec "$NAME" rm -rf /tmp/vekn-import
docker cp . "$NAME":/tmp/vekn-import
docker exec "$NAME" sh -c "cp $ROOT/Gemfile.lock /tmp/vekn-import/ && chown -R discourse:discourse /tmp/vekn-import"
run() {
    docker exec -u discourse:discourse -w "$ROOT" -e RAILS_ENV=production -e RAILS_DB=fr \
        -e DISCOURSE_ROOT="$ROOT" -e BUNDLE_GEMFILE=/tmp/vekn-import/Gemfile \
        -e IMPORT_SETTINGS=/tmp/vekn-import/phpbb-fr.yml "$NAME" "$@"
}
run bundle install --quiet
run bundle exec rails runner /tmp/vekn-import/prepare.rb
run bundle exec ruby script/import_scripts/phpbb3.rb /tmp/vekn-import/phpbb-fr.yml
run bundle exec rails runner /tmp/vekn-import/finish.rb
