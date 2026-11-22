#!/usr/bin/env bash
# Sequential polite crawl of the remaining online, authorised sites.
cd /home/ben/ECTI-Archive/runtime
while read -r name host; do
  [ -d ../ecti-archive-site/site/$name ] && [ "$(find ../ecti-archive-site/site/$name -type f | wc -l)" -gt 5 ] && { echo "$name: skipped (already has files)"; continue; }
  ./crawl.sh "$name" "$host"
  sleep 20
done <<'LIST'
ecticard2010 ecticard2010.ecticard.org
ecticard2011 ecticard2011.ecticard.org
ecticard2012 ecticard2012.ecticard.org
ecticard2013 ecticard2013.ecticard.org
ecticard2014 ecticard2014.ecticard.org
ecticard2015 ecticard2015.ecticard.org
ecticard2016 ecticard2016.ecticard.org
ecticard2019 ecticard2019.ecticard.org
ecticard2022 ecticard2022.ecticard.org
ecticard2023 ecticard2023.ecticard.org
ecticon2010 ecticon2010.ecticon.org
ecticon2012 ecticon2012.ecticon.org
ecticon2013 ecticon2013.ecticon.org
ecticon2014 ecticon2014.ecticon.org
ecticon2015 ecticon2015.ecticon.org
ecticon2019 ecticon2019.ecticon.org
ecticon2023 ecticon2023.ecticon.org
iscit2024 iscit2024.ecti-thailand.org
itccscc2026 itc-cscc2026.ecti-thailand.org
LIST
echo "ALL DONE"
