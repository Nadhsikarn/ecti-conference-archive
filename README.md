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
- ecticard2018, ecticard2020, ecticon2020 and ecticon2021 had no usable backup (blank WordPress,
  no database) and their servers are gone, so they were rebuilt from the Internet Archive
  Wayback Machine (`tools/wayback.py`). Wayback kept the pages and PDFs but not the theme CSS or
  most images, so these four sites show as plain, unstyled pages.
  เว็บสี่เว็บนี้กู้จาก Wayback Machine ได้เฉพาะเนื้อหาและ PDF ไม่มี CSS/รูป จึงแสดงเป็นหน้าเรียบๆ
- `tools/landing.py` generates `site/index.html`.
