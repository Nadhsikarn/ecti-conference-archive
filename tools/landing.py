#!/usr/bin/env python3
"""Generate the archive landing page.

usage: landing.py <site_root>     writes <site_root>/index.html and .nojekyll
Lists only sites whose folder exists under <site_root>.
"""
import sys, html, pathlib

root = pathlib.Path(sys.argv[1])

SERIES = [
    ("ECTI-CARD", "การประชุมวิชาการงานวิจัยและพัฒนาเชิงประยุกต์ (ECTI-CARD)",
     "ECTI Conference on Application Research and Development", "ecticard", range(2010, 2024)),
    ("ECTI-CON", "การประชุมวิชาการนานาชาติ ECTI-CON",
     "International Conference on Electrical Engineering/Electronics, Computer, Telecommunications and Information Technology",
     "ecticon", range(2010, 2024)),
    ("ICA-SYMP", "ICA-SYMP",
     "ICA-SYMP", "icasymp", range(2023, 2027)),
    ("ISCIT", "International Symposium on Communications and Information Technologies",
     "ISCIT", "iscit", range(2024, 2025)),
    ("ITC-CSCC", "International Technical Conference on Circuits/Systems, Computers and Communications",
     "ITC-CSCC", "itccscc", range(2026, 2027)),
]

sections = []
total = 0
for short, th, en, prefix, years in SERIES:
    items = []
    for y in years:
        d = root / f"{prefix}{y}"
        if (d / "index.html").is_file():
            items.append(f'<li><a href="{prefix}{y}/"><span class="yr">{y}</span>'
                         f'<span class="nm">{html.escape(short)} {y}</span></a></li>')
    if not items:
        continue
    total += len(items)
    sections.append(f"""<section>
  <h2>{html.escape(short)}</h2>
  {f'<p class="sub">{html.escape(en)}</p>' if en != short else ''}
  <ul>{''.join(items)}</ul>
</section>""")

page = f"""<!doctype html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ECTI Conference Archive</title>
<meta name="description" content="Archived websites of ECTI Association conferences (ECTI-CARD, ECTI-CON, ICA-SYMP, ISCIT, ITC-CSCC).">
<meta name="robots" content="index, follow">
<style>
:root {{ --bg:#fbfaf7; --fg:#1d1d1b; --muted:#6b6a64; --line:#e4e1d8; --card:#ffffff; --accent:#8a1c1c; }}
@media (prefers-color-scheme: dark) {{
  :root {{ --bg:#151514; --fg:#ecebe6; --muted:#a19f97; --line:#2e2d2a; --card:#1d1c1a; --accent:#e0827a; }}
}}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--fg);
  font:16px/1.55 "Sarabun","Noto Sans Thai",system-ui,-apple-system,"Segoe UI",sans-serif; }}
main {{ max-width:960px; margin:0 auto; padding:48px 16px 64px; }}
header {{ border-bottom:1px solid var(--line); padding-bottom:24px; margin-bottom:32px; }}
h1 {{ font-size:clamp(1.6rem,4vw,2.3rem); line-height:1.2; margin:0 0 8px; letter-spacing:-.01em; }}
header p {{ margin:4px 0; color:var(--muted); max-width:60ch; }}
section {{ margin:0 0 36px; }}
h2 {{ font-size:1.15rem; margin:0; color:var(--accent); letter-spacing:.02em; }}
.sub {{ margin:2px 0 12px; color:var(--muted); font-size:.92rem; }}
ul {{ list-style:none; padding:0; margin:0; display:grid; gap:8px;
  grid-template-columns:repeat(auto-fill,minmax(150px,1fr)); }}
li a {{ display:flex; flex-direction:column; padding:12px 14px; background:var(--card);
  border:1px solid var(--line); border-radius:8px; color:inherit; text-decoration:none;
  transition:border-color .15s, transform .15s; }}
li a:hover, li a:focus-visible {{ border-color:var(--accent); transform:translateY(-1px); outline:none; }}
.yr {{ font-size:1.35rem; font-weight:600; font-variant-numeric:tabular-nums; }}
.nm {{ font-size:.85rem; color:var(--muted); }}
footer {{ border-top:1px solid var(--line); padding-top:16px; color:var(--muted); font-size:.85rem; }}
@media (prefers-reduced-motion: reduce) {{ li a {{ transition:none; }} li a:hover {{ transform:none; }} }}
</style>
</head>
<body>
<main>
<header>
  <h1>ECTI Conference Archive</h1>
  <p>คลังเว็บไซต์งานประชุมวิชาการของสมาคม ECTI ที่ปิดไปแล้ว เก็บไว้เป็นสำเนาแบบอ่านอย่างเดียว</p>
  <p>Read-only snapshots of past ECTI Association conference websites. Forms, registration and paper submission no longer work.</p>
</header>
{chr(10).join(sections)}
<footer>{total} archived sites · Snapshot taken 2026</footer>
</main>
</body>
</html>
"""
(root / "index.html").write_text(page, encoding="utf-8")
(root / ".nojekyll").write_text("", encoding="utf-8")
print(f"wrote {root/'index.html'} with {total} sites")
