#!/usr/bin/env python3
"""Offline link check of a static mirror, optionally filling gaps from the backup.

usage: linkcheck.py <site_dir> [--fill <backup_dir>] [--missing-out=<file>]
Reports root-relative links (they break under /<repo>/<site>/) and relative links whose
target file is missing. With --fill: copies missing safe static files from the backup,
rewrites root-relative links to relative ones when the target exists, and writes paths
still missing (candidates for a Drive pull) to --missing-out.
"""
import os, re, sys, html, shutil, pathlib, urllib.parse, collections

site = pathlib.Path(sys.argv[1]).resolve()
backup = pathlib.Path(sys.argv[sys.argv.index("--fill") + 1]).resolve() if "--fill" in sys.argv else None
mo = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--missing-out=")), None)

STATIC = {".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp", ".bmp",
          ".woff", ".woff2", ".ttf", ".eot", ".otf", ".pdf", ".swf", ".doc", ".docx", ".ppt", ".pptx"}
BLOCK = re.compile(r"(^|/)(submission|user_files|updraft|ai1wm-backups|administrator|wp-admin)(/|$)"
                   r"|wp-config|configuration\.php|\.pem$|\.key$|\.sql$", re.I)
attr = re.compile(r'(\b(?:href|src|data-src|poster)\s*=\s*["\'])([^"\']+)(["\'])', re.I)
cssu = re.compile(r'(url\(\s*["\']?)([^"\')]+)(["\']?\s*\))')
SKIP = re.compile(r"^(#|data:|mailto:|tel:|javascript:|about:|\{|__ORIGIN|[a-z][a-z0-9+.-]*:|//)", re.I)

rootrel, missing, want = collections.Counter(), collections.Counter(), set()
copied = fixed = 0


def fill(rel):
    """Make site/rel exist by copying from backup. Returns True if it exists afterwards."""
    global copied
    t = site / rel
    if t.is_file():
        return True
    if backup is None or BLOCK.search(rel) or pathlib.PurePosixPath(rel).suffix.lower() not in STATIC:
        return False
    src = backup / rel
    if src.is_file() and src.stat().st_size <= 50_000_000:
        t.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, t)
        copied += 1
        return True
    want.add(rel)
    return False


def check(p, regex, s):
    def repl(m):
        global fixed
        raw = m.group(2)
        u = html.unescape(raw.strip())
        if not u or SKIP.match(u):
            return m.group(0)
        path = urllib.parse.unquote(u.split("#")[0].split("?")[0])
        if not path:
            return m.group(0)
        if u.startswith("/"):
            rel = path.lstrip("/")
            if (site / rel).is_dir():
                rel = rel.rstrip("/") + "/index.html"
            if fill(rel):
                new = urllib.parse.quote(os.path.relpath(site / rel, p.parent), safe="/%-._~")
                fixed += 1
                return m.group(1) + new + m.group(3)
            rootrel[u] += 1
            return m.group(0)
        t = (p.parent / path).resolve()
        if t.is_dir():
            t = t / "index.html"
        if t.exists():
            return m.group(0)
        try:
            rel = str(t.relative_to(site))
        except ValueError:
            missing[f"(outside) {u}"[:140]] += 1
            return m.group(0)
        if not fill(rel):
            missing[f"{p.relative_to(site).parent}/{u}"[:140]] += 1
        return m.group(0)
    return regex.sub(repl, s)


for p in list(site.rglob("*")):
    if not p.is_file() or p.suffix.lower() not in (".html", ".htm", ".css"):
        continue
    s = p.read_text("utf-8", "ignore")
    n = s
    if p.suffix.lower() != ".css":
        n = check(p, attr, n)
    n = check(p, cssu, n)
    if n != s and backup is not None:
        p.write_text(n, "utf-8")

if mo:
    pathlib.Path(mo).write_text("".join(w + "\n" for w in sorted(want)))
extra = f", copied {copied}, root-rel fixed {fixed}, to pull {len(want)}" if backup else ""
print(f"{site.name}: root-relative {sum(rootrel.values())} ({len(rootrel)} distinct), "
      f"missing targets {sum(missing.values())} ({len(missing)} distinct){extra}")
for k, c in rootrel.most_common(4):
    print(f"   ROOT {c:4d} {k[:120]}")
for k, c in missing.most_common(6):
    print(f"   MISS {c:4d} {k}")
