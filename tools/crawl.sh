#!/usr/bin/env bash
# usage: crawl.sh <name> <host>  -> /home/ben/ECTI-Archive/ecti-archive-site/site/<name>
# Polite archive crawl of a site the owner has authorised us to archive.
set -u
name=$1; host=$2
out=/home/ben/ECTI-Archive/ecti-archive-site/site
mkdir -p "$out/../logs" "$out/$name"
cd "$out/$name" || exit 1
wget --mirror --page-requisites --convert-links --adjust-extension --no-parent \
  --no-host-directories --restrict-file-names=windows \
  --wait=1 --random-wait --tries=2 --timeout=30 --quota=1g --reject='*.mpg,*.mpeg,*.mp4,*.mov,*.avi,*.zip,*.wpress,*.iso,*.rar,*.7z' \
  --user-agent="ECTI-archive-bot (site archiving by the site administrator)" \
  --reject-regex='(wp-login|wp-admin|xmlrpc|/feed|replytocom=|[?&]s=|wp-json|[?&]share=|/embed/|lostpassword|wp-comments-post)' \
  -o "../../logs/$name.log" "https://$host/"
echo "$name: exit $? size $(du -sh . | cut -f1) files $(find . -type f | wc -l)"
