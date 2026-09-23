#!/usr/bin/env python3
"""Print CitySwift's Greenhouse jobs with url + updated_at."""
import json

d = json.load(open("/home/ubuntu/job-hunt-scratch/cityswift_api.json"))
for j in d["jobs"]:
    print("%-58s | %-45s | %s | %s" % (j["title"][:58], j["location"]["name"][:45],
                                       j["updated_at"], j["absolute_url"]))
