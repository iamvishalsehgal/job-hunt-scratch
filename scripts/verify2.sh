#!/bin/bash
# Verify the Intact own-board req and the Version 1 own-board req; capture salary/language evidence.
set -u
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"
S=/home/ubuntu/job-hunt-scratch
curl -sS -L --max-time 30 -A "$UA" "https://careers.rsagroup.ie/jobs/view/2921" -o "$S/intact_2921.html"
echo "intact 2921 bytes: $(wc -c < $S/intact_2921.html)"
curl -sS -L --max-time 30 -A "$UA" "https://version1.com/en-us/careers/job-listing/data-engineer-microsoft-fabric-ref6496s" -o "$S/version1_req.html"
echo "version1 bytes: $(wc -c < $S/version1_req.html)"
echo "=== intact 2921 title/ref ==="
grep -io "Data Engineer[^<]\{0,60\}" "$S/intact_2921.html" | head -4
grep -io "SSIS\|SQL Server\|SAS\|Dundrum\|reference[^<]\{0,40\}" "$S/intact_2921.html" | sort -u | head -12
echo "=== version1 salary/ref ==="
grep -io "EUR [0-9,]\{4,9\}\|ref6496s\|Salary[^<]\{0,60\}" "$S/version1_req.html" | sort -u | head -10
