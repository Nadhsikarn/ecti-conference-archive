# ECTI Conference Archive

Read-only static snapshots of past ECTI Association conference websites
(ECTI-CARD, ECTI-CON, ICA-SYMP, ISCIT, ITC-CSCC), published with GitHub Pages at
https://ectipr.github.io/ecti-conference-archive/

The ECTI Association's own website is archived separately in
[ectipr/ecti-archive](https://github.com/ectipr/ecti-archive) (https://ectipr.github.io/ecti-archive/).

คลังเว็บไซต์งานประชุมวิชาการของสมาคม ECTI ที่ปิดไปแล้ว เก็บเป็นหน้าเว็บแบบ static อ่านอย่างเดียว
(ฟอร์ม ลงทะเบียน และส่งบทความใช้งานไม่ได้)

## Layout / โครงสร้าง

| Path | What |
|---|---|
| `docs/` | The published site (GitHub Pages: branch `main`, folder `/docs`). `docs/index.html` lists every archived conference; each conference is in `docs/<name>/`. |
| `tools/` | Scripts used to build the snapshots (crawl, mirror a local Docker copy, fix links, build). |
| `EXCLUDE.md` | What was deliberately left out (author submissions, configs, databases, keys, backups). |

## Large files / ไฟล์ขนาดใหญ่

- ECTI-CARD 2019 and 2022 proceedings PDFs (65 MB, 77 MB) are not duplicated here: the pages link
  to the copies in [ectipr/ecti-archive](https://github.com/ectipr/ecti-archive) `documents/`.
- The ECTI-CARD 2019 photo galleries were resized to 2048 px; the full-resolution originals
  (634 MB zip) go in this repository's GitHub Release `assets-v1`.

Proceedings ECTI-CARD 2019/2022 ลิงก์ไปที่ไฟล์ใน repo ecti-archive ส่วนรูปต้นฉบับ ECTI-CARD 2019 อยู่ใน Release `assets-v1`

## Publishing / การเผยแพร่

Settings → Pages → Deploy from a branch → `main` / `/docs`. The absolute URLs some WordPress pages
need are already filled in for `https://ectipr.github.io/ecti-conference-archive/`
(`tools/build.py` does this for another URL).

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
- `tools/landing.py` generates `docs/index.html`.
