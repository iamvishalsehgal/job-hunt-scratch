#!/bin/bash
# Fetch the Intact/RSA Ireland vacancy list + the resolved ATS boards, then grep locally.
set -u
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"
S=/home/ubuntu/job-hunt-scratch
curl -sS -L --max-time 30 -A "$UA" "https://careers.rsagroup.ie/vacancyList.php" -o "$S/intact_vacancies.html"
echo "intact vacancy list bytes: $(wc -c < $S/intact_vacancies.html)"
curl -sS -L --max-time 30 -A "$UA" "https://job-boards.greenhouse.io/doitintl/jobs/7990925003" -o "$S/doit_gh.html"
echo "doit bytes: $(wc -c < $S/doit_gh.html)"
curl -sS -L --max-time 30 -A "$UA" "https://jobs.ashbyhq.com/primer.io" -o "$S/primer_ashby.html"
echo "primer board bytes: $(wc -c < $S/primer_ashby.html)"
curl -sS -L --max-time 30 -A "$UA" "https://www.gea.com/en/careers/apply-now/item/?job=JR-0040297" -o "$S/gea_req.html"
echo "gea bytes: $(wc -c < $S/gea_req.html)"
