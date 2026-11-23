#!/usr/bin/env python3
"""Fill missing theme/plugin/core files of a static mirror from an unpacked official release.

usage: fill_from_dir.py <site_dir> <host> <url_prefix>=<source_dir> [...]
  e.g. fill_from_dir.py site/ecticon2021 ecticon2021.ecticon.org \
         wp-content/themes/ashe=third-party/ashe.1.8.2/ashe wp-includes=third-party/wordpress-5.4.4/wordpress/wp-includes

Only files the pages actually reference (and that are missing) are copied; only static
file types (css/js/images/fonts), never PHP. Repeats once for assets referenced by new CSS.
"""
import re, sys, shutil, pathlib

here = pathlib.Path(__file__).resolve().parent
site, host = pathlib.Path(sys.argv[1]).resolve(), sys.argv[2]
maps = [a.split("=", 1) for a in sys.argv[3:]]
SAFE = re.compile(r"\.(css|js|png|jpe?g|gif|svg|ico|webp|bmp|woff2?|ttf|eot|otf|json)$", re.I)

# reuse the reference scanner from wayback_fill.py (without its network part)
src = (here / "wayback_fill.py").read_text().split("def get(")[0]
ns = {"__name__": "scan"}
argv, sys.argv = sys.argv, ["x", str(site), host]
exec(src, ns)
sys.argv = argv

copied = 0
for _ in range(3):
    n = 0
    for rel in ns["wanted"]():
        if not SAFE.search(rel):
            continue
        for prefix, d in maps:
            if rel.startswith(prefix.rstrip("/") + "/"):
                s = pathlib.Path(d) / rel[len(prefix.rstrip("/")) + 1:]
                if s.is_file():
                    t = site / rel
                    t.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(s, t)
                    n += 1
                break
    copied += n
    if not n:
        break
print(f"{site.name}: copied {copied} files from official releases; still missing {len(ns['wanted']())}")
