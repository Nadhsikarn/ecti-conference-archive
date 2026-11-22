#!/usr/bin/env python3
"""Copy a post-processed site to <dest> filling in the __ORIGIN__ token.

usage: build.py <site_dir> <dest_dir> <origin_url> [<release_base_url>]
  e.g. build.py site/icasymp2025 dist/icasymp2025 https://USER.github.io/REPO/icasymp2025 \
       https://github.com/USER/REPO/releases/download/assets-v1
__RELEASE__ (links to files moved to GitHub Releases) is filled with release_base_url.
"""
import sys, shutil, pathlib, urllib.parse

src, dst, origin = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), sys.argv[3].rstrip("/")
release = sys.argv[4].rstrip("/") if len(sys.argv) > 4 else None
if dst.exists():
    shutil.rmtree(dst)
shutil.copytree(src, dst)
enc = urllib.parse.quote(origin, safe="")
n = 0
for p in dst.rglob("*"):
    if not p.is_file():
        continue
    try:
        s = p.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        continue
    if "__ORIGIN" in s or (release and "__RELEASE__" in s):
        s = s.replace("__ORIGIN_ENC__", enc).replace("__ORIGIN__", origin)
        if release:
            s = s.replace("__RELEASE__", release)
        p.write_text(s, encoding="utf-8")
        n += 1
print(f"built {dst} ({n} files rewritten) with origin {origin}")
