#!/usr/bin/env python3
"""Rebuild a static copy of a dead site from the Internet Archive (Wayback Machine).

usage: wayback.py <host> <out_dir> [<from_ts> <to_ts>]   (e.g. 202205 202207: only captures in that window)
  e.g. wayback.py ecticon2020.ecticon.org ecti-archive-site/site/ecticon2020

1. list captured URLs (status 200, one per URL) from the CDX API;
2. download each page/file in raw mode (".../web/<ts>id_/<url>": original bytes, no toolbar);
3. download same-host page requisites (css/js/images/fonts) referenced by pages and CSS,
   letting Wayback pick the nearest capture;
Files are stored at their URL path (dirs get index.html; "?p=1" pages become "index@p=1.html").
4. rewrite links between captured pages/files to relative paths (run localize.py afterwards
   for anything else). Resumable: files already on disk and URLs that 404'd before are skipped.
Polite: sequential, delay between requests, backoff on 429.
"""
import os, re, sys, json, time, html, pathlib, urllib.parse, urllib.request, urllib.error

host, out = sys.argv[1], pathlib.Path(sys.argv[2])
WINDOW = f"&from={sys.argv[3]}&to={sys.argv[4]}" if len(sys.argv) > 4 else ""
UA = "ECTI-archive-bot (restoring the site administrator's own conference sites)"
DELAY = 3.0
SKIP = re.compile(r"wp-json|xmlrpc|wp-login|wp-admin|/feed/?$|/comments/|/submission(/|$)|[?&](s|replytocom|share|feed|format|print|tmpl|task|rest_route)=|/embed/?$", re.I)
STATIC = re.compile(r"\.(css|js|png|jpe?g|gif|svg|ico|webp|bmp|woff2?|ttf|eot|otf|pdf|docx?|pptx?|xlsx?)$", re.I)
logdir = out.parent.parent / "logs"
log = open(logdir / f"{out.name}-wayback.log", "a", encoding="utf-8", buffering=1) if logdir.is_dir() else sys.stderr
failfile = logdir / f"{out.name}-wayback-404.txt"
known404 = set(failfile.read_text().split()) if failfile.is_file() else set()
fail404 = open(failfile, "a", encoding="utf-8", buffering=1) if logdir.is_dir() else None
urlmap = {}   # key(url) -> local file


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
    if p.query and not is_html and not STATIC.search(p.path):
        return None
    if p.query and is_html:           # /content/?p=12 -> content/index@p=12.html
        d, _, base = path.rpartition("/")
        base = re.sub(r"\.(html?|php)$", "", base) or "index"
        q = re.sub(r"[^A-Za-z0-9=_.-]+", "_", urllib.parse.unquote(p.query.replace("&amp;", "&")))[:80]
        rel = f"{d}/{base}@{q}.html".lstrip("/")
        return None if ".." in rel.split("/") else out / rel
    if path.endswith("/"):
        path += "index.html"
    elif is_html and not re.search(r"\.html?$", path, re.I):
        path += ".html"         # /about or /x.php -> about.html / x.php.html, same folder so relative links keep working
    rel = path.lstrip("/")
    if ".." in rel.split("/"):
        return None
    return out / rel


def norm(u):
    p = urllib.parse.urlsplit(u)
    netloc = p.hostname or ""
    return urllib.parse.urlunsplit(("https", netloc, p.path, p.query, ""))


def key(u):
    p = urllib.parse.urlsplit(html.unescape(u))
    q = p.query.replace("&amp;", "&")
    return urllib.parse.unquote(p.path or "/") + ("?" + q if q else "")


def save(u, ts, is_html=None):
    if u in known404:
        return None
    if is_html is not None:
        pre = local_path(u, is_html)
        if pre is not None and pre.is_file() and pre.stat().st_size > 0:
            urlmap[key(u)] = pre
            print(f"HAVE {u}", file=log)
            return pre, pre.read_bytes(), "text/html" if is_html else ""
    status, body, ctype = get(f"https://web.archive.org/web/{ts}id_/{u}")
    if status != 200 or not body or b"Internet Archive: Temporarily Offline" in body[:3000]:
        print(f"FAIL {status} {u}", file=log)
        if status == 404 and fail404:
            print(u, file=fail404)
        return None
    if is_html is None:
        is_html = "html" in ctype
    dst = local_path(u, is_html)
    if dst is None:
        return None
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(body)
    urlmap[key(u)] = dst
    print(f"OK {u} -> {dst.relative_to(out)}", file=log)
    return dst, body, ctype


cdx = (f"https://web.archive.org/cdx/search/cdx?url={host}/*&output=json"
       f"&filter=statuscode:200&collapse=urlkey&fl=timestamp,original,mimetype{WINDOW}")
status, body, _ = get(cdx)
rows = json.loads(body)[1:] if status == 200 and body.strip() else []
# also the bare host (homepage) in case the wildcard misses it
status, body, _ = get(f"https://web.archive.org/cdx/search/cdx?url={host}/&output=json&filter=statuscode:200&fl=timestamp,original,mimetype&limit=-1{WINDOW}")
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

# 4. rewrite links between captured files to relative paths
link = re.compile(r'(\b(?:href|src)\s*=\s*["\'])([^"\']+)(["\'])', re.I)
rewritten = 0
for u, ts, _ in pages:
    f = urlmap.get(key(u))
    if f is None or not f.is_file():
        continue
    text = f.read_text("utf-8", "ignore")
    bm = re.search(r'<base\s+href\s*=\s*["\']([^"\']*)["\']', text, re.I)
    base_url = urllib.parse.urljoin(u, html.unescape(bm.group(1))) if bm and bm.group(1).strip() else u
    text = re.sub(r'<base\s[^>]*>\s*', "", text, flags=re.I)   # links below become relative to the file itself

    def rl(m):
        global rewritten
        v = html.unescape(m.group(2).strip())
        if not v or v.startswith(("#", "data:", "mailto:", "javascript:")):
            return m.group(0)
        a = urllib.parse.urljoin(base_url, v)
        sp = urllib.parse.urlsplit(a)
        if sp.hostname != host:
            return m.group(0) if base_url == u else m.group(1) + a + m.group(3)
        k = key(a.split("#")[0])
        t = (urlmap.get(k) or urlmap.get(k.rstrip("/") + "/") or urlmap.get(k + "/")
             or (urlmap.get(k.split("?")[0]) if STATIC.search(sp.path) else None))
        if t is None:   # not captured: keep it pointing where the original did
            return m.group(0) if base_url == u else m.group(1) + a + m.group(3)
        rel = urllib.parse.quote(os.path.relpath(t, f.parent), safe="/%-._~@=")
        frag = "#" + sp.fragment if sp.fragment else ""
        rewritten += 1
        return m.group(1) + rel + frag + m.group(3)

    new = link.sub(rl, text)
    if new != text:
        f.write_text(new, "utf-8")
print(f"links rewritten: {rewritten}", file=log)

files = sum(1 for p in out.rglob("*") if p.is_file())
print(f"{out.name}: cdx rows {len(rows)}, pages {len(pages)}, files {files}, links rewritten {rewritten}")
