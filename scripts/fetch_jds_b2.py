import json, urllib.request, os, sys

OUT = os.path.expanduser("~/job-hunt-scratch/jd_raw")
os.makedirs(OUT, exist_ok=True)

def post(url, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json",
                 "User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode()

def get(url):
    req = urllib.request.Request(url, headers={"Accept": "application/json",
        "User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode()

targets = [
    ("euronext", "https://hrhub.wd3.myworkdayjobs.com/wday/cxs/hrhub/Euronext_Career_Page/job/Dublin/Data-Engineer-for-AI_R28530", "post"),
    ("salesforce", "https://salesforce.wd12.myworkdayjobs.com/wday/cxs/salesforce/External_Career_Site/job/Ireland---Dublin/Data-Engineering-Senior-Associate_JR359930", "post"),
    ("basicfit", "https://basicfit.wd103.myworkdayjobs.com/wday/cxs/basicfit/BasicFit_Career_Site_NL/job/Hoofddorp/Club-Data-Analyst_R55713", "post"),
    ("jpmc", "https://jpmc.fa.oraclecloud.com/hcmRestApi/resources/latest/recruitingCEJobRequisitionDetails?expand=all&onlyData=true&finder=ByRequisitionId;requisitionId=210768004,siteNumber=CX_1001", "get"),
]

for name, url, meth in targets:
    try:
        txt = post(url, {}) if meth == "post" else get(url)
        p = os.path.join(OUT, name + ".json")
        open(p, "w").write(txt)
        print(name, "OK", len(txt), p)
    except Exception as e:
        print(name, "FAIL", type(e).__name__, str(e)[:200])
