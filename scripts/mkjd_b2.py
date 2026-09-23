import json, urllib.request, urllib.error, os, re, html

WS = "/home/ubuntu/.hermes/profiles/vishal/workspace"
RAW = os.path.expanduser("~/job-hunt-scratch/jd_raw")

def fetch(url):
    req = urllib.request.Request(url, headers={"Content-Type": "application/json",
        "Accept": "application/json", "Accept-Language": "en-US",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]

def html2text(s):
    s = re.sub(r"(?i)<br\s*/?>", "\n", s)
    s = re.sub(r"(?i)</(p|div|li|h1|h2|h3|h4|tr|ul|ol)>", "\n", s)
    s = re.sub(r"(?i)<li[^>]*>", "- ", s)
    s = re.sub(r"(?i)<h([1-6])[^>]*>", "\n## ", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n\s*\n\s*\n+", "\n\n", s)
    return s.strip()

JOBS = {
 "euronext-data-engineer-for-ai": ("euronext", "https://hrhub.wd3.myworkdayjobs.com/wday/cxs/hrhub/Euronext_Career_Page/job/Dublin/Data-Engineer-for-AI_R28530"),
 "salesforce-data-engineering-senior-associate": ("salesforce", "https://salesforce.wd12.myworkdayjobs.com/wday/cxs/salesforce/External_Career_Site/job/Ireland---Dublin/Data-Engineering-Senior-Associate_JR359930"),
 "basic-fit-club-data-analyst": ("basicfit", "https://basicfit.wd103.myworkdayjobs.com/wday/cxs/basicfit/BasicFit_Career_Site_NL/job/Hoofddorp/Club-Data-Analyst_R55713"),
}
for slug, (key, api) in JOBS.items():
    st, txt = fetch(api)
    if st != 200:
        print("fail", slug, st); continue
    j = json.loads(txt)["jobPostingInfo"]
    body = html2text(j.get("jobDescription", ""))
    open(os.path.join(RAW, key + ".txt"), "w").write(body)
    print("==", slug, "|", j.get("title"), "|", j.get("location"), "| chars", len(body))

# JPMC full fields
st, txt = fetch("https://jpmc.fa.oraclecloud.com/hcmRestApi/resources/latest/recruitingCEJobRequisitions"
                "?onlyData=true&expand=all&finder=findReqs;siteNumber=CX_1001,limit=10,keyword=210768004")
print("jpmc expand=all", st, len(txt))
if st == 200:
    open(os.path.join(RAW, "jpmc_all.json"), "w").write(txt)
    d = json.loads(txt)
    rl = d["items"][0].get("requisitionList") or []
    if rl:
        it = rl[0]
        for k, v in it.items():
            if v not in (None, "", [], {}):
                print("  ", k, "=", str(v)[:160].replace("\n", " "))
