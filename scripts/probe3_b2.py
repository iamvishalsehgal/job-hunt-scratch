import json, urllib.request, urllib.error, os, re, html

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

# JPMC via search list
u = ("https://jpmc.fa.oraclecloud.com/hcmRestApi/resources/latest/recruitingCEJobRequisitions"
     "?onlyData=true&expand=requisitionList.secondaryLocations,requisitionList.otherWorkLocations"
     "&finder=findReqs;siteNumber=CX_1001,limit=10,keyword=210768004")
st, txt = fetch(u)
print("jpmc list", st, len(txt))
open(os.path.join(OUT, "jpmc_list.json"), "w").write(txt)
try:
    d = json.loads(txt)
    rl = d["items"][0].get("requisitionList") or []
    for r in rl:
        print(r.get("Id"), "|", r.get("Title"), "|", r.get("PostedDate"), "|", r.get("PrimaryLocation"))
    if rl:
        open(os.path.join(OUT, "jpmc_list_item.json"), "w").write(json.dumps(rl[0], indent=1))
        print(json.dumps(rl[0])[:1200])
except Exception as e:
    print("parse fail", e, txt[:300])

# Workday status fields
for n in ("euronext", "salesforce", "basicfit"):
    p = os.path.join(OUT, n + ".json")
    if n == "euronext":
        u2 = "https://hrhub.wd3.myworkdayjobs.com/wday/cxs/hrhub/Euronext_Career_Page/job/Dublin/Data-Engineer-for-AI_R28530"
        st2, txt2 = fetch(u2)
        if st2 == 200:
            open(p, "w").write(txt2)
    if not os.path.exists(p):
        print(n, "missing"); continue
    j = json.loads(open(p).read())["jobPostingInfo"]
    print("==", n, "|", j.get("title"), "|", j.get("location"), "| start", j.get("startDate"),
          "| end", j.get("endDate"), "| posted", j.get("postedOn"), "| externalUrl", j.get("externalUrl"))
