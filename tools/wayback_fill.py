#!/usr/bin/env python3
"""Fill files missing from a static mirror using the Wayback Machine.

usage: wayback_fill.py <site_dir> <host> [<host2> ...]

Scans HTML/CSS in <site_dir> for references to static files (images, css, js, fonts,
documents) that point inside the site (relative, root-relative or absolute to one of the
site's own hosts) but do not exist locally, then asks Wayback for the nearest capture
("web/2up_/..."-style raw id_ fetch) and saves it at the referenced path.
Run localize.py afterwards so absolute links to the hosts point at the new files.
Polite: sequential, 3 s between requests, backoff on 429/5xx, remembers 404s.
"""
import os, re, sys, html, time, pathlib, urllib.parse, urllib.request, urllib.error

site = pathlib.Path(sys.argv[1]).resolve()
hosts = sys.argv[2:]
UA = "ECTI-archive-bot (restoring the site administrator's own conference sites)"
DELAY = 3.0
m = re.search(r"(20\d\d)", site.name)
TS = (m.group(1) if m else "2020") + "0601"
STATIC = re.compile(r"\.(css|js|png|jpe?g|gif|svg|ico|webp|bmp|woff2?|ttf|eot|otf|pdf|docx?|pptx?|xlsx?|swf)$", re.I)
BLOCK = re.compile(r"(^|/)(submission|user_files|updraft|ai1wm-backups|wp-admin|administrator)(/|$)", re.I)
logdir = site.parent.parent / "logs"
logdir.mkdir(exist_ok=True)
log = open(logdir / f"{site.name}-wayback-fill.log", "a", encoding="utf-8", buffering=1)
f404 = logdir / f"{site.name}-wayback-fill-404.txt"
known404 = set(f404.read_text().split()) if f404.is_file() else set()
f404h = open(f404, "a", encoding="utf-8", buffering=1)

attr = re.compile(r'\b(?:href|src|data-src|data-lazy-src|poster|background)\s*=\s*["\']([^"\']+)["\']', re.I)
srcset = re.compile(r'\bsrcset\s*=\s*["\']([^"\']+)["\']', re.I)
cssu = re.compile(r'url\(\s*["\']?([^"\')]+)["\']?\s*\)')


def wanted():
    out = {}
    for p in site.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in (".html", ".htm", ".css") and "@" not in p.name:
            continue
        try:
            t = p.read_text("utf-8", "ignore")
        except OSError:
            continue
        refs = attr.findall(t) + cssu.findall(t)
        for s in srcset.findall(t):
            refs += [x.strip().split(" ")[0] for x in s.split(",")]
        for r in refs:
            r = html.unescape(r.strip())
            if not r or r.startswith(("#", "data:", "mailto:", "javascript:", "__ORIGIN", "__RELEASE", "{")):
                continue
            r = r.replace("\\", "/")
            sp = urllib.parse.urlsplit(r)
            if sp.scheme in ("http", "https") or r.startswith("//"):
                if (sp.hostname or "") not in hosts:
                    continue
                rel = urllib.parse.unquote(sp.path).lstrip("/")
            elif sp.scheme:
                continue
            elif r.startswith("/"):
                rel = urllib.parse.unquote(sp.path).lstrip("/")
            else:
                full = (p.parent / urllib.parse.unquote(sp.path)).resolve()
                try:
                    rel = str(full.relative_to(site))
                except ValueError:
                    continue
            if not rel or not STATIC.search(rel) or BLOCK.search(rel) or ".." in rel.split("/"):
                continue
            if (site / rel).exists():
                continue
            out.setdefault(rel, sp.query)
    return out


def get(url, tries=4):
    for i in range(tries):
        time.sleep(DELAY)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            if e.code in (429, 502, 503, 504):
                time.sleep(20 * (i + 1)); continue
            return e.code, b""
        except Exception as e:
            print(f"retry {url}: {e}", file=log); time.sleep(10 * (i + 1))
    return 0, b""


got = tried = 0
for rnd in range(2):                      # 2nd round: assets referenced by newly fetched CSS
    todo = wanted()
    todo = {k: v for k, v in todo.items() if k not in known404}
    if not todo:
        break
    for rel, q in todo.items():
        ok = False
        for h in hosts:
            for scheme in ("http",):          # Wayback treats http/https as the same URL
                u = f"{scheme}://{h}/{urllib.parse.quote(rel)}"
                key = f"{h}/{rel}"
                if key in known404:
                    continue
                tried += 1
                st, body = get(f"https://web.archive.org/web/{TS}id_/{u}")
                if st == 200 and body and b"Internet Archive: Temporarily Offline" not in body[:3000] \
                        and not (rel.lower().endswith((".png", ".jpg", ".jpeg", ".gif")) and body[:15].lower().startswith((b"<!doctype", b"<html"))):
                    dst = site / rel
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    dst.write_bytes(body)
                    print(f"OK {u}", file=log)
                    got += 1; ok = True
                    break
                print(f"FAIL {st} {u}", file=log)
                if st == 404:
                    known404.add(key); print(key, file=f404h)
            if ok:
                break
        if not ok:
            known404.add(rel); print(rel, file=f404h)

left = len(wanted())
print(f"{site.name}: fetched {got} from Wayback ({tried} requests), still missing {left}")
