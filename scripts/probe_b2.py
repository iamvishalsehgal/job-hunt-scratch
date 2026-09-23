import json, urllib.request, urllib.error, os

OUT = os.path.expanduser("~/job-hunt-scratch/jd_raw")
os.makedirs(OUT, exist_ok=True)

def fetch(url, method="GET", body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
        headers={"Content-Type": "application/json", "Accept": "application/json",
                 "Accept-Language": "en-US", "User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:400]
    except Exception as e:
        return -1, f"{type(e).__name__}: {e}"

tests = [
  ("euronext_get", "GET", "https://hrhub.wd3.myworkdayjobs.com/wday/cxs/hrhub/Euronext_Career_Page/job/Dublin/Data-Engineer-for-AI_R28530", None),
  ("euronext_body", "POST", "https://hrhub.wd3.myworkdayjobs.com/wday/cxs/hrhub/Euronext_Career_Page/job/Dublin/Data-Engineer-for-AI_R28530", {"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": ""}),
  ("jpmc_a", "GET", "https://jpmc.fa.oraclecloud.com/hcmRestApi/resources/latest/recruitingCEJobRequisitionDetails?expand=all&onlyData=true&finder=ByRequisitionId;requisitionId=210768004,siteNumber=CX_1001", None),
]
for name, meth, url, body in tests:
    st, txt = fetch(url, meth, body)
    print("==", name, st, len(txt))
    print(txt[:350].replace("\n", " "))
