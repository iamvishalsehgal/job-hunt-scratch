#!/bin/bash
# Check CitySwift's Greenhouse board for the Analytics Engineer req and its publication date.
set -u
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"
S=/home/ubuntu/job-hunt-scratch
curl -sS -L --max-time 30 -A "$UA" "https://job-boards.greenhouse.io/cityswift" -o "$S/cityswift_gh.html"
echo "cityswift board bytes: $(wc -c < $S/cityswift_gh.html)"
grep -io "analytics engineer[^<]\{0,80\}" "$S/cityswift_gh.html" | head -5
echo "--- job links ---"
grep -io "job-boards.greenhouse.io/cityswift/jobs/[0-9]*" "$S/cityswift_gh.html" | sort -u | head -10
echo "--- gea ireland board probe ---"
curl -sS -L --max-time 30 -A "$UA" "https://www.gea.com/en/careers/apply-now/index.jsp?country=Ireland" -o "$S/gea_ie.html"
echo "gea ie bytes: $(wc -c < $S/gea_ie.html)"
grep -io "JR-00[0-9]*" "$S/gea_ie.html" | sort -u | head -20
