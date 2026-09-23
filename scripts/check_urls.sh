#!/bin/bash
# HTTP status probe for the finalist apply URLs + Intact careers page fetch.
set -u
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"
probe() {
  local code
  code=$(curl -sS -o /dev/null -w "%{http_code}" -L --max-time 25 -A "$UA" "$1")
  echo "$code  $1"
}
probe "https://intactinsurance.ie/careers"
probe "https://www.gea.com/en/careers/apply-now/item/?job=JR-0040297"
probe "https://version1.com/en-us/careers/job-listing/data-engineer-microsoft-fabric-ref6496s"
probe "https://job-boards.greenhouse.io/doitintl/jobs/7990925003"
probe "https://jobs.ashbyhq.com/primer.io/49e633ec-f5de-42f1-8db9-6a6ea86142bf"
probe "https://sandboxinteractive.teamtailor.com/jobs/8316016-data-engineer-m-f-d"
probe "https://jobs.smartrecruiters.com/Version1/744000131483999-data-engineer-microsoft-fabric"
curl -sS -L --max-time 25 -A "$UA" "https://intactinsurance.ie/careers" -o /home/ubuntu/job-hunt-scratch/intact_careers.html
echo "intact bytes: $(wc -c < /home/ubuntu/job-hunt-scratch/intact_careers.html)"
