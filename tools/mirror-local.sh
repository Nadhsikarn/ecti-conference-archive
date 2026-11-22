#!/usr/bin/env bash
# usage: mirror-local.sh <site> <port>   -- wget mirror of a locally running WP (docker) into ecti-archive-site/site/<site>
set -u
name=$1; port=$2
out=/home/ben/ECTI-Archive/ecti-archive-site/site
mkdir -p "$out/../logs" "$out/$name"; cd "$out/$name" || exit 1
wget --mirror --page-requisites --convert-links --adjust-extension --no-parent \
  --no-host-directories --restrict-file-names=windows -e robots=off --tries=2 --timeout=60 \
  --reject-regex='(wp-login|wp-admin|xmlrpc|/feed|replytocom=|[?&]s=|wp-json|rest_route|[?&]share=|/embed/|lostpassword|wp-comments-post|/author/|[?&]p=)' \
  --reject='*.wpress,*.zip,*.sql' \
  -o "../../logs/$name-local.log" "http://localhost:$port/"
echo "$name: exit $? size $(du -sh . | cut -f1) files $(find . -type f | wc -l)"
