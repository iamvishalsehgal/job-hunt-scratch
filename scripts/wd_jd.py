#!/usr/bin/env python3
"""Fetch a Workday CXS job posting JSON and write the JD text.

Usage: python3 wd_jd.py <tenant.wdN.myworkdayjobs.com> <site> <job-path> <out.md>
Example: python3 wd_jd.py vanderlande.wd3.myworkdayjobs.com careers "job/Veghel/Integration-Engineer_JR37386" <out.md>
Writes title, external url and plain-text JD to <out.md>. Exit 0 ok, 1 fail.
"""
import html
import json
import pathlib
import re
import sys
import urllib.request


def get(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/126 Safari/537.36",
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")


def main():
    if len(sys.argv) != 5:
        print(__doc__)
        return 2
    host, site, jpath, out = sys.argv[1:5]
    jpath = jpath.lstrip("/")
    url = f"https://{host}/wday/cxs/{host.split('.')[0]}/{site}/{jpath}"
    try:
        data = json.loads(get(url))
    except Exception as e:
        print("FAIL", url, e)
        return 1
    info = data.get("jobPostingInfo", {}) or {}
    txt = info.get("jobDescription", "") or ""
    txt = re.sub(r"<br\s*/?>", "\n", txt)
    txt = re.sub(r"</(p|li|div|h\d)>", "\n", txt)
    txt = re.sub(r"<li>", "- ", txt)
    txt = re.sub(r"<[^>]+>", "", txt)
    txt = html.unescape(txt)
    txt = re.sub(r"\n{3,}", "\n\n", txt).strip()
    body = (
        f"# {info.get('title','')} - {data.get('hiringOrganization',{}).get('name','')}\n\n"
        f"externalUrl: {info.get('externalUrl','')}\n"
        f"postedOn: {info.get('postedOn','')} | timeType: {info.get('timeType','')} | "
        f"jobReqId: {info.get('jobRequisitionId','')}\n"
        f"location: {info.get('location','')} | additionalLocations: {info.get('additionalLocations','')}\n"
        f"canApply: {info.get('canApply')} | startDate: {info.get('startDate','')}\n\n"
        f"{txt}\n"
    )
    p = pathlib.Path(out)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    print("ok", out, p.stat().st_size, "bytes | canApply=", info.get("canApply"), "|", info.get("title"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
