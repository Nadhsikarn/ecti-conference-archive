#!/usr/bin/env bash
# usage: pull-site.sh <site>  -- full WP site folder from Drive, minus backups/keys/caches
set -u
n=$1
rclone copy "gdrive:volume/$n" "/home/ben/ECTI-Archive/ECTI-Drive-sites/$n" \
  --drive-root-folder-id "$ECTI_DRIVE_FOLDER_ID" \
  --filter '- *.pem' --filter '- *.key' --filter '- *.wpress' --filter '- *.sql' --filter '- *.sql.gz' \
  --filter '- /wp-content/updraft/**' --filter '- /wp-content/ai1wm-backups/**' --filter '- /wp-content/cache/**' \
  --filter '- /wp-content/uploads/backup*/**' --filter '+ **' \
  --transfers 16 --checkers 16 --log-level INFO --stats 60s --log-file "/home/ben/ECTI-Archive/rclone-$n.log"
echo "$n: exit $? files $(find /home/ben/ECTI-Archive/ECTI-Drive-sites/$n -type f | wc -l)"
