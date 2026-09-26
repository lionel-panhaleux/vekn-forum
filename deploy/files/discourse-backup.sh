#!/bin/bash
# Each Discourse site writes a daily archive (database and uploads) under backups/<db>/ and keeps
# the last few; restic keeps the history, deduplicating the archives already pushed.
set -euo pipefail
export RESTIC_REPOSITORY="$RESTIC_REPOSITORY_BASE/$RESTIC_REPO"
/usr/bin/restic cat config > /dev/null 2>&1 || /usr/bin/restic init
/usr/bin/restic backup /var/discourse/shared/web-only/backups
/usr/bin/restic forget --group-by host \
    --keep-daily "$REMOTE_KEEP_DAILY" \
    --keep-weekly "$REMOTE_KEEP_WEEKLY" \
    --keep-monthly "$REMOTE_KEEP_MONTHLY" --prune
