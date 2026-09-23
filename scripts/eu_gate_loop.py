#!/usr/bin/env python3
"""Run the EU scope gate on every captured JD + flag German-written / German-fluency postings."""
import json
import os
import re
import subprocess

WS = "/home/ubuntu/.hermes/profiles/vishal/workspace"
SCRATCH = "/home/ubuntu/job-hunt-scratch"
rows = json.load(open(os.path.join(SCRATCH, "eu_shortlist.json")))

COUNTRY = {"mastercard": "IE", "eir-business-talent": "IE", "musgrave": "IE", "euronext": "IE",
           "workday": "IE", "version-1": "IE", "creditsafe-group": "IE", "cityswift": "IE",
           "block-labs": "IE", "doit": "IE", "gea-group": "IE", "primer": "IE",
           "intact-insurance-ie": "IE", "jpmorganchase": "IE", "fulcrum-digital": "IE"}
GERMAN_HINT = ["deutschkenntnisse", "deutsch", "german", "fließend", "fliessend", "verhandlungssicher",
               "muttersprache", "sprachkenntnisse", "kenntnisse in deutsch"]
GERMAN_WORDS = ["und ", "mit ", "wir ", "sie ", "für ", "aufgaben", "anforderungen", "kenntnisse",
                "erfahrung", "team", "dich", "deine", "unser", "ist ", "sind ", "als "]
REQ_MARK = re.compile(r"(?i)(fluen|fluency|native|C1|C2|B2|kenntnisse|proficien|command of|"
                      r"spoken and written|working language|language)")
out = []
for r in rows:
    if not r["path"] or not os.path.exists(r["path"]):
        out.append(dict(r, gate_rc=None, gate_out="(no jd)", german="(no jd)"))
        continue
    txt = open(r["path"], errors="replace").read()
    cc = COUNTRY.get(r["company"], "DE")
    cp = subprocess.run(["python3", os.path.join(WS, "gates/eu_scope_gate.py"), "check",
                         "--country", cc, "--jd", r["path"]],
                        capture_output=True, text=True, cwd=WS)
    gate_out = (cp.stdout + cp.stderr).strip()
    low = txt.lower()
    hints = sorted({h for h in GERMAN_HINT if h in low})
    gw = sum(1 for w in GERMAN_WORDS if w in low)
    german = "hints=%s german_word_score=%d" % (",".join(hints) or "-", gw)
    out.append(dict(r, gate_rc=cp.returncode, gate_out=gate_out, german=german))
    print("=" * 100)
    print("%s | %s | %s | rc=%d" % (r["company"], r["role"], cc, cp.returncode))
    print(gate_out)
    print("[lang] " + german)
    for line in txt.splitlines():
        if REQ_MARK.search(line) and ("deutsch" in line.lower() or "english" in line.lower()
                                      or "german" in line.lower() or "sprach" in line.lower()):
            print("   >> " + line.strip()[:300])
json.dump(out, open(os.path.join(SCRATCH, "eu_gate.json"), "w"), indent=1)
