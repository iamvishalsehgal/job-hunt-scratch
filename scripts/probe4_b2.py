import json, urllib.request, urllib.error, os, re, html

RAW = os.path.expanduser("~/job-hunt-scratch/jd_raw")

def fetch(url, hdr=None):
    h = {"Accept": "application/json", "Accept-Language": "en-US",
         "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}
    if hdr: h.update(hdr)
    req = urllib.request.Request(url, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read().decode(errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")[:300]
    except Exception as e:
        return -1, str(e)[:200]

B = "https://jpmc.fa.oraclecloud.com"
tries = [
 ("v1", B + "/hcmRestApi/resources/latest/recruitingCEJobRequisitionDetails?expand=all&onlyData=true&finder=ByRequisitionId;requisitionId=210768004"),
 ("v2", B + "/hcmRestApi/resources/latest/recruitingCEJobRequisitionDetails?expand=all&onlyData=true&finder=ByRequisitionNumber;requisitionNumber=210768004,siteNumber=CX_1001"),
 ("v3", B + "/hcmRestApi/resources/latest/recruitingCEJobRequisitions?onlyData=true&expand=requisitionList.requisitionFlexFields,requisitionList.secondaryLocations,requisitionList.otherWorkLocations&finder=findReqs;siteNumber=CX_1001,limit=5,keyword=Databricks"),
 ("html", B + "/hcmUI/CandidateExperience/en/sites/CX_1001/job/210768004"),
]
for n, u in tries:
    st, t = fetch(u)
    print("==", n, st, len(t))
    if n == "v3" and st == 200:
        open(os.path.join(RAW, "jpmc_v3.json"), "w").write(t)
        d = json.loads(t)
        for r in (d["items"][0].get("requisitionList") or []):
            print("   ", r.get("Id"), r.get("Title"), [k for k, v in r.items() if v not in (None, "", [], {})][:25])
    elif n == "html" and st == 200:
        open(os.path.join(RAW, "jpmc_page.html"), "w").write(t)
        m = re.findall(r"(?:Databricks|Qualifications|Responsibilities)[^<\"]{0,120}", t)
        print("   hits:", m[:6])
    else:
        print("   ", t[:200].replace("\n", " "))
