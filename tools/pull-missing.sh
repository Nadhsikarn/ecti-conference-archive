#!/usr/bin/env bash
# usage: pull-missing.sh <list_dir>   (one <site>.txt per site, paths relative to volume/<site>)
# Downloads only the listed static files from Drive into ECTI-Drive-sites/<site>/
set -u
for f in "$1"/*.txt; do
  n=$(basename "$f" .txt); [ -s "$f" ] || continue
  rclone copy "gdrive:volume/$n" "/home/ben/ECTI-Archive/ECTI-Drive-sites/$n" \
    --drive-root-folder-id "${ECTI_DRIVE_FOLDER_ID:?set ECTI_DRIVE_FOLDER_ID}" --files-from-raw "$f" \
 --transfers 8 --log-level ERROR 2>&1 | grep -v "client_id" 
  echo "$n: $(find /home/ben/ECTI-Archive/ECTI-Drive-sites/$n -type f 2>/dev/null | wc -l) files"
done
