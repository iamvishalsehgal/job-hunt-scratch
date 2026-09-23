#!/usr/bin/env python3
"""Print kept cards as 'id | country | posted | company | title | location'."""
import json
import os

SCRATCH = "/home/ubuntu/job-hunt-scratch"
kept = json.load(open(os.path.join(SCRATCH, "eu_kept.json")))
for c in sorted(kept, key=lambda x: (x["country"] != "IE", x["posted"]), reverse=True):
    print("%s | %s | %s | %s | %s | %s" % (c["id"], c["country"], c["posted"],
                                           c["company"], c["title"], c["location"]))
