import json, os
p='/home/ubuntu/.hermes/profiles/vishal/cron/jobs.json'
d=json.load(open(p))
for j in d.get('jobs',[]):
    print(j.get('id'), '|', j.get('name'), '|', j.get('schedule'), '|en=', j.get('enabled'), '|last=', j.get('last_status'), '|len=', len(j.get('prompt') or ''))
