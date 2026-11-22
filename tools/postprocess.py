#!/usr/bin/env python3
"""Post-process a wget mirror of a local WordPress site for static hosting.

usage: postprocess.py <site_dir> [<local_origin>]   (default origin: http://localhost:18081)

- removes <link> tags that only make sense with a live WordPress (feeds, oEmbed, REST, RSD, shortlink)
- replaces the local origin with the token __ORIGIN__ (filled in by build.py at publish time)
Idempotent: running twice changes nothing more.
"""
import re, sys, pathlib

site = pathlib.Path(sys.argv[1])
origin = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:18081"
esc = origin.replace("/", r"\/")                 # JSON-escaped form  http:\/\/localhost:18081
host = origin.split("//", 1)[1]                  # localhost:18081
enc = re.escape(host.replace(":", "%3A"))        # url-encoded form inside query strings

drop_link = re.compile(
    r'<link\b[^>]*?(?:rel=["\'](?:https://api\.w\.org/|EditURI|shortlink)["\']'
    r'|type=["\'](?:application/rss\+xml|application/json\+oembed|text/xml\+oembed|application/json)["\']'
    r'|href=["\'][^"\']*(?:/feed/|xmlrpc\.php|wp-json/)[^"\']*["\'])[^>]*?>\s*',
    re.I,
)

TEXT = {".html", ".htm", ".css", ".js", ".json", ".xml", ".svg", ".txt"}
changed = removed = 0
for p in site.rglob("*"):
    if not p.is_file() or p.suffix.lower() not in TEXT and not p.name.endswith(".css") and "@ver" not in p.name:
        continue
    try:
        s = p.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        continue
    if host not in s and esc not in s and "%3A" not in s:
        continue
    o = s
    if p.suffix.lower() in (".html", ".htm"):
        s, n = drop_link.subn("", s)
        removed += n
    s = s.replace(origin, "__ORIGIN__").replace(esc, "__ORIGIN__")
    s = re.sub(r"http%3A%2F%2F" + enc, "__ORIGIN_ENC__", s)
    if s != o:
        p.write_text(s, encoding="utf-8")
        changed += 1
print(f"files changed: {changed}, <link> tags removed: {removed}")
left = sum(1 for p in site.rglob("*") if p.is_file() and not p.is_symlink()
           and host.encode() in p.read_bytes()[:5_000_000])
print(f"files still containing '{host}': {left}")
