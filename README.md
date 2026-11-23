# ECTI Conference Archive

Read-only static snapshots of past ECTI Association conference websites
(ECTI-CARD, ECTI-CON, ICA-SYMP, ISCIT, ITC-CSCC), published with GitHub Pages.

คลังเว็บไซต์งานประชุมวิชาการของสมาคม ECTI ที่ปิดไปแล้ว เก็บเป็นหน้าเว็บแบบ static อ่านอย่างเดียว
(ฟอร์ม ลงทะเบียน และส่งบทความใช้งานไม่ได้)

## Layout / โครงสร้าง

| Path | What |
|---|---|
| `site/` | The published site. `site/index.html` lists every archived conference; each conference is in `site/<name>/`. |
| `tools/` | Scripts used to build the snapshots (crawl, mirror a local Docker copy, fix links, build). |
| `EXCLUDE.md` | What was deliberately left out (author submissions, configs, databases, keys, backups). |

## Large files / ไฟล์ขนาดใหญ่

Files over 50 MB and the original full-resolution ECTI-CARD 2019 photos are attached to the
GitHub Release tagged `assets-v1`, not stored in the repository.

ไฟล์เกิน 50 MB และรูปต้นฉบับความละเอียดเต็มของ ECTI-CARD 2019 อยู่ใน GitHub Release แท็ก `assets-v1`

## Publishing / การเผยแพร่

Some pages contain placeholder tokens that must be filled before publishing:

- `__ORIGIN__` / `__ORIGIN_ENC__`: the site's public URL (e.g. `https://USER.github.io/REPO/icasymp2025`)
- `__RELEASE__`: the release download base (e.g. `https://github.com/USER/REPO/releases/download/assets-v1`)

`tools/build.py <site_dir> <dest_dir> <origin_url> [<release_base_url>]` copies a site and fills them in.

## How the snapshots were made / วิธีทำ

- Sites still online were crawled politely from their own domains (`tools/crawl.sh`).
- Offline WordPress sites were restored from the server backup, run locally in Docker
  (`tools/docker-compose.yml`) and mirrored with wget (`tools/mirror-local.sh`).
- `tools/postprocess.py`, `tools/localize.py` and `tools/linkcheck.py` make every site self-contained
  and working under a sub-path; missing assets were filled from the backup.
- ecticard2014 (WordPress 3.8) and ecticard2016 (Joomla) need old PHP: they were run from the
  backup in a local PHP 5.6 container (`tools/php56/Dockerfile`) and mirrored the same way.
- Sites with no usable backup and no live server were rebuilt from the Internet Archive Wayback
  Machine (`tools/wayback.py`, `tools/wayback_fill.py`): ecticard2009, ecticard2018, ecticard2020,
  ecticon2009, ecticon2011 (www.ecti-con2011.org), ecticon2016 (www.ecticon2016.org),
  ecticon2020, ecticon2021 and ecticon2022 (www.ecti-con2022.org, May 2022 captures only; later
  captures of that domain are spam). Wayback kept the pages and PDFs but often not the theme CSS
  or images. For free WordPress themes/plugins/core the exact released versions were taken from
  wordpress.org (`tools/fill_from_dir.py`), so ecticard2020, ecticon2021 and ecticon2022 have
  their styling back; the others show as plain pages.
  เว็บที่ไม่มี backup ใช้ได้ กู้จาก Wayback Machine ได้เนื้อหาและ PDF ส่วน CSS/รูปบางเว็บไม่มี จึงแสดงเป็นหน้าเรียบๆ
- Never captured anywhere (backup, server, Wayback): ecticard2017, ecticard2021, ecticon2017,
  ecticon2018 (only hosting placeholders and the paper-submission system, which is excluded).
- `tools/landing.py` generates `site/index.html`.
