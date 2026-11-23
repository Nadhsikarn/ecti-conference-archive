#!/usr/bin/env python3
"""Make a crawled site self-contained.

usage: localize.py <site_dir> <host> <backup_dir> [--dry]
  e.g. localize.py site/ecticard2013 ecticard2013.ecticard.org work/volume/ecticard2013

For every absolute link to the site's own host (http/https, also JSON-escaped):
  - if the target is a static file missing from the mirror but present in the
    backup, copy it in (never .php / config / keys / submission data);
  - if the target now exists in the mirror, rewrite the link to a relative path;
  - otherwise leave it (counted as "unresolved": dynamic pages, admin-ajax...).
CSS copied from the backup is scanned for url(...) so its images come too.
Idempotent.
"""
import os, re, sys, shutil, pathlib, urllib.parse

site = pathlib.Path(sys.argv[1]).resolve()
host = sys.argv[2]
backup = pathlib.Path(sys.argv[3]).resolve()
dry = "--dry" in sys.argv

STATIC = {".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp",
          ".woff", ".woff2", ".ttf", ".eot", ".otf", ".pdf", ".swf", ".bmp", ".json", ".doc", ".docx", ".ppt", ".pptx"}
BLOCK = re.compile(r"(^|/)(submission|user_files|updraft|ai1wm-backups|administrator|wp-admin)(/|$)"
                   r"|wp-config|configuration\.php|\.pem$|\.key$|\.sql$", re.I)
TEXT = {".html", ".htm", ".css", ".js", ".json", ".xml", ".svg"}

hq = re.escape(host)
url_re = re.compile(r"https?:(?://|\\/\\/)" + hq + r"((?:/|\\/)[^\"'\s<>)\\]*(?:\\/[^\"'\s<>)\\]*)*)?")
css_url = re.compile(r"url\(\s*['\"]?([^'\")]+)['\"]?\s*\)")


def local_path(urlpath):
    """URL path -> relative file path inside the mirror, or None for queries/dirs."""
    p = urlpath.replace("\\/", "/").split("#", 1)[0]
    if "?" in p or "&amp;" in p:
        base, _, q = p.partition("?")
        # a static file with a cache-buster (?ver=1.2) is the same file
        if pathlib.Path(base).suffix.lower() in STATIC:
            p = base
        else:
            # a page with a query: wget --restrict-file-names=windows saved it as <path>@<query>.html
            b = urllib.parse.unquote(base).lstrip("/")
            b = (b + "index.html") if (not b or b.endswith("/")) else b
            cand = f"{b}@{q.replace('&amp;', '&')}.html"
            return cand if (site / cand).is_file() else None
    p = urllib.parse.unquote(p).lstrip("/")
    return p or None


def fetch_from_backup(rel):
    """Copy rel from backup into the mirror if it is a safe static file. Returns True if present."""
    dst = site / rel
    if dst.is_file():
        return True
    if pathlib.Path(rel).suffix.lower() not in STATIC or BLOCK.search(rel):
        return False
    src = backup / rel
    if not src.is_file() or src.stat().st_size > 50_000_000:
        missing.add(rel)
        return False
    if not dry:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    copied.append(rel)
    if rel.lower().endswith(".css"):
        scan_css(rel, src.read_text("utf-8", "ignore"))
    return True


def scan_css(rel, text):
    base = pathlib.PurePosixPath(rel).parent
    for u in css_url.findall(text):
        if u.startswith(("data:", "http:", "https:", "//", "#")):
            continue
        target = os.path.normpath(str(base / u.split("?")[0].split("#")[0]))
        if not target.startswith(".."):
            fetch_from_backup(target)


copied, rewritten, unresolved, missing = [], 0, {}, set()
files = [p for p in site.rglob("*") if p.is_file() and (p.suffix.lower() in TEXT or "@" in p.name)]
for p in files:
    try:
        s = p.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        continue
    if host not in s:
        continue
    here = p.parent
    escaped_ctx = p.suffix.lower() in (".js", ".json")

    def repl(m):
        global rewritten
        whole, path = m.group(0), m.group(1) or "/"
        tail = ""
        ent = re.search(r"&(?:apos|quot|#0?39|#34);.*$", path)
        if ent:  # url(&apos;...&apos;) in inline styles: keep the entity outside the URL
            tail = path[ent.start():]
            path = path[:ent.start()]
            whole = whole[:len(whole) - len(tail)]
        rel = local_path(path)
        if rel is None:
            if path in ("/", "\\/"):
                rel = "index.html"
            else:
                unresolved[whole] = unresolved.get(whole, 0) + 1
                return whole + tail
        if (site / rel).is_dir():
            rel = rel.rstrip("/") + "/index.html"
        if not fetch_from_backup(rel) and not (site / rel).is_file():
            unresolved[whole] = unresolved.get(whole, 0) + 1
            return whole + tail
        out = os.path.relpath(site / rel, here).replace(os.sep, "/")
        out = urllib.parse.quote(out, safe="/%-._~")
        if "\\/" in whole:
            out = out.replace("/", "\\/")
        rewritten += 1
        return out + tail

    new = url_re.sub(repl, s)
    if new != s and not dry:
        p.write_text(new, encoding="utf-8")

mo = next((a.split("=",1)[1] for a in sys.argv if a.startswith("--missing-out=")), None)
if mo:
    pathlib.Path(mo).write_text("".join(m + "\n" for m in sorted(missing)))
print(f"{site.name}: copied from backup {len(copied)}, links rewritten {rewritten}, "
      f"unresolved {sum(unresolved.values())} ({len(unresolved)} distinct)")
for u, n in sorted(unresolved.items(), key=lambda x: -x[1])[:15]:
    print(f"   {n:4d}  {u}")
