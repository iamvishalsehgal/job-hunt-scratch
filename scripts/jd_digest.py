#!/usr/bin/env python3
"""Per-JD digest: header, seniority, salary/permit/sponsor lines, skill hits."""
import json
import os
import re

SCRATCH = "/home/ubuntu/job-hunt-scratch"
rows = json.load(open(os.path.join(SCRATCH, "eu_shortlist.json")))
SKILLS = ["azure", "databricks", "snowflake", "dbt", "sql server", "fabric", "synapse",
          "data factory", "pyspark", "spark", "airflow", "power bi", "python", "kafka",
          "knowledge graph", "ontology", "rag", "llm", "neo4j", "data vault", "ssis",
          "integration", "etl", "api", "teradata", "oracle", "gcp", "bigquery", "aws",
          "git", "ci/cd", "docker", "postgres", "mongodb", "graph", "semantic", "vector"]
MARK = re.compile(r"(?i)(salary|€|eur|gross|per month|per annum|package|compensation|"
                  r"visa|sponsor|permit|work authoris|work authoriz|right to work|"
                  r"years of experience|\d\+\s*years|senior|junior|mid-level|fluen|"
                  r"language|deutsch|german)")

only = [r for r in rows if r["company"] in (
    "mastercard", "eir-business-talent", "musgrave", "euronext", "workday", "version-1",
    "creditsafe-group", "cityswift", "block-labs", "doit", "gea-group", "primer",
    "intact-insurance-ie", "jpmorganchase", "fulcrum-digital", "sandbox-interactive",
    "rheindata", "jobspace", "dymatrix", "dataciders")]
for r in only:
    if not r["path"] or not os.path.exists(r["path"]):
        continue
    txt = open(r["path"], errors="replace").read()
    low = txt.lower()
    print("=" * 110)
    print(txt.split("## Job description")[0].strip())
    hits = [s for s in SKILLS if s in low]
    print("SKILLS: " + ", ".join(hits))
    n_de = sum(1 for w in (" und ", " wir ", " für ", " mit ", " dich", " dein", " Kenntnisse",
                           " Erfahrung", " Aufgaben", " Suche", " bieten", " über ")
               if w.lower() in low)
    print("GERMAN-WRITTEN score: %d (>=6 = German JD)" % n_de)
    print("-- marked lines --")
    seen = set()
    for line in txt.splitlines():
        s = line.strip()
        if s and MARK.search(s) and len(s) < 400 and s not in seen:
            seen.add(s)
            print("   " + s[:380])
