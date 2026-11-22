#!/usr/bin/env python3
"""Rebuild a static copy of a dead site from the Internet Archive (Wayback Machine).

usage: wayback.py <host> <out_dir>
  e.g. wayback.py ecticon2020.ecticon.org ecti-archive-site/site/ecticon2020

1. list captured URLs (status 200, one per URL) from the CDX API;
2. download each page/file in raw mode (".../web/<ts>id_/<url>": original bytes, no toolbar);
3. download same-host page requisites (css/js/images/fonts) referenced by pages and CSS,
   letting Wayback pick the nearest capture;
Files are stored at their URL path (dirs get index.html). Links are NOT rewritten here:
run localize.py afterwards. Polite: sequential, delay between requests, backoff on 429.
"""
import re, sys, json, time, html, pathlib, urllib.parse, urllib.request, urllib.error

host, out = sys.argv[1], pathlib.Path(sys.argv[2])
UA = "ECTI-archive-bot (restoring the site administrator's own conference sites)"
DELAY = 3.0
SKIP = re.compile(r"wp-json|xmlrpc|wp-login|wp-admin|/feed/?$|/comments/|/submission(/|$)|[?&](s|replytocom|share)=|/embed/?$", re.I)
STATIC = re.compile(r"\.(css|js|png|jpe?g|gif|svg|ico|webp|bmp|woff2?|ttf|eot|otf|pdf|docx?|pptx?|xlsx?)$", re.I)
log = open(out.parent.parent / "logs" / f"{out.name}-wayback.log", "a", encoding="utf-8") \
    if (out.parent.parent / "logs").is_dir() else sys.stderr


def get(url, tries=4):
    for i in range(tries):
        time.sleep(DELAY)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.status, r.read(), r.headers.get("Content-Type", "")
        except urllib.error.HTTPError as e:
            if e.code in (429, 502, 503, 504):
                time.sleep(20 * (i + 1)); continue
            return e.code, b"", ""
        except Exception as e:
            print(f"retry {url}: {e}", file=log); time.sleep(10 * (i + 1))
    return 0, b"", ""


def local_path(u, is_html):
    p = urllib.parse.urlsplit(u)
    path = urllib.parse.unquote(p.path) or "/"
    if p.query and (is_html or not STATIC.search(p.path)):
        return None   # dynamic page; static assets keep their path, query dropped
    if path.endswith("/"):
        path += "index.html"
    elif is_html and not re.search(r"\.html?$", path, re.I):
        path += "/index.html"   # pretty permalink without trailing slash
    rel = path.lstrip("/")
    if ".." in rel.split("/"):
        return None
    return out / rel


def norm(u):
    p = urllib.parse.urlsplit(u)
    netloc = p.hostname or ""
    return urllib.parse.urlunsplit(("https", netloc, p.path, p.query, ""))


def save(u, ts, is_html=None):
    status, body, ctype = get(f"https://web.archive.org/web/{ts}id_/{u}")
    if status != 200 or not body or b"Internet Archive: Temporarily Offline" in body[:3000]:
        print(f"FAIL {status} {u}", file=log); return None
    if is_html is None:
        is_html = "html" in ctype
    dst = local_path(u, is_html)
    if dst is None:
        return None
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(body)
    print(f"OK {u} -> {dst.relative_to(out)}", file=log)
    return dst, body, ctype


cdx = (f"https://web.archive.org/cdx/search/cdx?url={host}/*&output=json"
       f"&filter=statuscode:200&collapse=urlkey&fl=timestamp,original,mimetype")
status, body, _ = get(cdx)
rows = json.loads(body)[1:] if status == 200 and body.strip() else []
# also the bare host (homepage) in case the wildcard misses it
status, body, _ = get(f"https://web.archive.org/cdx/search/cdx?url={host}/&output=json&filter=statuscode:200&fl=timestamp,original,mimetype&limit=-1")
if status == 200 and body.strip():
    rows += json.loads(body)[1:]

seen, pages, todo_assets = set(), [], {}
for ts, orig, mime in rows:
    u = norm(orig)
    if u in seen or SKIP.search(u) or urllib.parse.urlsplit(u).hostname != host:
        continue
    seen.add(u)
    r = save(u, ts, is_html=("html" in mime))
    if r and "html" in mime:
        pages.append((u, ts, r[1]))

attr = re.compile(r'\b(?:href|src|data-src|data-lazy-src)\s*=\s*["\']([^"\']+)["\']', re.I)
srcset = re.compile(r'\bsrcset\s*=\s*["\']([^"\']+)["\']', re.I)
cssu = re.compile(r'url\(\s*["\']?([^"\')]+)["\']?\s*\)')


def collect(base, text, ts):
    refs = attr.findall(text) + cssu.findall(text)
    for s in srcset.findall(text):
        refs += [x.strip().split(" ")[0] for x in s.split(",")]
    for r in refs:
        r = html.unescape(r.strip())
        if not r or r.startswith(("data:", "#", "mailto:", "javascript:")):
            continue
        a = norm(urllib.parse.urljoin(base, r))
        sp = urllib.parse.urlsplit(a)
        if sp.hostname != host or not STATIC.search(sp.path) or SKIP.search(a):
            continue
        a = urllib.parse.urlunsplit(("https", host, sp.path, sp.query, ""))
        if a not in seen:
            todo_assets.setdefault(a, ts)


for u, ts, body in pages:
    collect(u, body.decode("utf-8", "ignore"), ts)

rounds = 0
while todo_assets and rounds < 3:
    rounds += 1
    batch, todo_assets = todo_assets, {}
    for a, ts in batch.items():
        if a in seen:
            continue
        seen.add(a)
        r = save(a, ts, is_html=False)
        if not r and "?" in a:        # captured without the ?ver= query?
            r = save(a.split("?", 1)[0], ts, is_html=False)
        if r and a.lower().endswith(".css"):
            collect(a, r[1].decode("utf-8", "ignore"), ts)

files = sum(1 for p in out.rglob("*") if p.is_file())
print(f"{out.name}: cdx rows {len(rows)}, pages {len(pages)}, files {files}")
