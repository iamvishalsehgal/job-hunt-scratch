#!/usr/bin/env python3
"""Triage the 252 unique DE/IE cards: country resolve, freshness, tracker dedupe, title filter."""
import json
import os
import re

SCRATCH = "/home/ubuntu/job-hunt-scratch"
WS = "/home/ubuntu/.hermes/profiles/vishal/workspace"
TODAY = "2026-09-23"
CUTOFF = "2026-08-23"          # < 1 month old

cards = json.load(open(os.path.join(SCRATCH, "eu_cards.json")))
byid = {}
for c in cards:
    if c["id"] in byid:
        # keep the first, note the extra keyword hit
        byid[c["id"]]["kws"].append(c["kw"])
    else:
        c["kws"] = [c["kw"]]
        byid[c["id"]] = c
uniq = list(byid.values())
print("unique cards:", len(uniq))

DE_TOK = ["germany", "deutschland", "berlin", "munich", "münchen", "munchen", "hamburg", "frankfurt",
          "stuttgart", "cologne", "köln", "koln", "düsseldorf", "dusseldorf", "leipzig", "dresden",
          "nürnberg", "nurnberg", "nuremberg", "hannover", "hanover", "bremen", "dortmund", "essen",
          "bonn", "münster", "munster", "karlsruhe", "mannheim", "freiburg", "augsburg", "wiesbaden",
          "bielefeld", "bochum", "potsdam", "erlangen", "jena", "kiel", "aachen", "heidelberg",
          "mainz", "saarbrücken", "regensburg", "ulm", "wolfsburg", "ingolstadt", "bonn"]
IE_TOK = ["ireland", "dublin", "cork", "galway", "limerick", "waterford", "donegal", "kerry",
          "sligo", "athlone", "dundalk", "maynooth", "clontarf", "kildare", "wicklow", "meath",
          "leitrim", "tipperary", "wexford", "kilkenny", "shannon"]
OTHER = ["england", "london", "united kingdom", "netherlands", "amsterdam", "poland", "warsaw",
         "sweden", "stockholm", "spain", "madrid", "france", "paris", "italy", "milan", "portugal",
         "lisbon", "belgium", "brussels", "austria", "vienna", "wien", "switzerland", "zurich",
         "denmark", "copenhagen", "norway", "oslo", "finland", "helsinki", "romania", "bucharest",
         "india", "bengaluru", "bangalore", "united states", "new york", "boston", "greece", "athens",
         "hungary", "budapest", "czech", "prague", "united arab emirates", "dubai", "lithuania",
         "vilnius", "bulgaria", "sofia", "croatia", "zagreb", "estonia", "tallinn", "latvia", "riga",
         "serbia", "belgrade", "turkey", "istanbul", "canada", "toronto", "singapore", "australia",
         "israel", "tel aviv", "japan", "tokyo", "china", "shanghai"]

BAD_TITLE = ["intern", "internship", "working student", "werkstudent", "praktikum", "apprentice",
             "graduate program", "phd", "doctoral", "postdoc", "sales", "account manager",
             "recruiter", "talent", "marketing", "pre-sales", "presales", "$", "principal",
             "staff", "director", "head of", "vp", "journeyman", "trainer", "teacher", "lecturer",
             "nurse", "physician", "clinical", "logistics", "warehouse", "driver", "technician",
             "electrician", "mechanic", "cook", "chef", "cleaner", "security officer", "study"]
GOOD_TITLE = ["data engineer", "analytics engineer", "data platform", "data warehouse", "etl",
              "elt", "integration engineer", "snowflake", "databricks", "azure data", "dbt",
              "data integration", "knowledge graph", "ontology", "semantic", "data architect",
              "bi engineer", "dwh", "database engineer", "data & analytics", "data and analytics",
              "analytics & data", "information engineer", "migration engineer", "data ops",
              "dataops", "sql developer", "fabric", "informatica", "ssis", "talend", "bot",
              "data model"]


def country_of(loc):
    low = (loc or "").lower()
    if re.search(r"(?<![a-z])(de|ie)(?![a-z])", low.split(",")[-1].strip()):
        pass
    for t in OTHER:
        if re.search(r"(?<![a-z])" + re.escape(t) + r"(?![a-z])", low):
            return "OUT"
    for t in DE_TOK:
        if re.search(r"(?<![a-z])" + re.escape(t) + r"(?![a-z])", low):
            return "DE"
    for t in IE_TOK:
        if re.search(r"(?<![a-z])" + re.escape(t) + r"(?![a-z])", low):
            return "IE"
    tail = (loc or "").strip().split(",")[-1].strip().lower()
    if tail in ("germany", "de"):
        return "DE"
    if tail in ("ireland", "ie"):
        return "IE"
    return "?"


tracker = [c.strip().lower() for c in json.load(open(os.path.join(SCRATCH, "dedupe.json")))["tracker"]]

kept, dropped = [], []
for c in uniq:
    cc = country_of(c["location"])
    c["country"] = cc
    reasons = []
    if cc not in ("DE", "IE"):
        reasons.append("country=" + cc)
    if not c["posted"]:
        reasons.append("no-posted-date")
    elif c["posted"] < CUTOFF:
        reasons.append("stale:" + c["posted"])
    tl = c["title"].lower()
    if any(b in tl for b in BAD_TITLE):
        reasons.append("bad-title")
    elif not any(g in tl for g in GOOD_TITLE):
        reasons.append("off-lane-title")
    if any(t in c["company"].lower() or c["company"].lower() in t for t in tracker if t):
        reasons.append("tracker-dup")
    if reasons:
        dropped.append((reasons, c))
    else:
        kept.append(c)

print("\nKEPT %d  DROPPED %d" % (len(kept), len(dropped)))
print("\n--- KEPT (title-filtered) ---")
for c in sorted(kept, key=lambda x: (x["country"], x["posted"]), reverse=True):
    print("%s | %s | %s | %s | %s | kw=%s" % (c["country"], c["posted"], c["company"],
                                              c["title"], c["location"], ",".join(c["kws"])))
print("\n--- DROPPED reasons histogram ---")
hist = {}
for r, c in dropped:
    for x in r:
        hist[x.split(":")[0]] = hist.get(x.split(":")[0], 0) + 1
print(hist)
json.dump(kept, open(os.path.join(SCRATCH, "eu_kept.json"), "w"), indent=1)
json.dump([{"r": r, "c": c} for r, c in dropped], open(os.path.join(SCRATCH, "eu_dropped.json"), "w"), indent=1)
