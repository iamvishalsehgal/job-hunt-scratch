import json, urllib.request, urllib.error, os

OUT = os.path.expanduser("~/job-hunt-scratch/jd_raw")
os.makedirs(OUT, exist_ok=True)

def fetch(url):
    req = urllib.request.Request(url, headers={"Content-Type": "application/json",
        "Accept": "application/json", "Accept-Language": "en-US",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]
    except Exception as e:
        return -1, f"{type(e).__name__}: {e}"

wd = [
 ("salesforce", "https://salesforce.wd12.myworkdayjobs.com/wday/cxs/salesforce/External_Career_Site/job/Ireland---Dublin/Data-Engineering-Senior-Associate_JR359930"),
 ("basicfit", "https://basicfit.wd103.myworkdayjobs.com/wday/cxs/basicfit/BasicFit_Career_Site_NL/job/Hoofddorp/Club-Data-Analyst_R55713"),
]
for n, u in wd:
    st, txt = fetch(u)
    print("==", n, st, len(txt))
    if st == 200:
        open(os.path.join(OUT, n + ".json"), "w").write(txt)
        print(json.loads(txt)["jobPostingInfo"]["title"], "|", json.loads(txt)["jobPostingInfo"].get("location"))

oracle = [
 ("enc1", "https://jpmc.fa.oraclecloud.com/hcmRestApi/resources/latest/recruitingCEJobRequisitionDetails?expand=all&onlyData=true&finder=ByRequisitionId%3BrequisitionId%3D210768004%2CsiteNumber%3DCX_1001"),
 ("enc2", "https://jpmc.fa.oraclecloud.com/hcmRestApi/resources/latest/recruitingCEJobRequisitionDetails?onlyData=true&expand=all&finder=ByRequisitionId;requisitionId=210768004,siteNumber=CX_1001;"),
 ("list", "https://jpmc.fa.oraclecloud.com/hcmRestApi/resources/latest/recruitingCEJobRequisitions?onlyData=true&expand=requisitionList.secondaryLocations&finder=findReqs;siteNumber=CX_1001,limit=10,keyword=210768004"),
]
for n, u in oracle:
    st, txt = fetch(u)
    print("==", n, st, len(txt))
    print(txt[:250].replace("\n", " "))
