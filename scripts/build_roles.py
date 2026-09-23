#!/usr/bin/env python3
"""Write the tier-1 EU (DE/IE) survivor roles file for the 20260923b sweep."""
import json
import os

WS = "/home/ubuntu/.hermes/profiles/vishal/workspace"
SCRATCH = "/home/ubuntu/job-hunt-scratch"
OUT = os.path.join(WS, "discovery", "eu_fresh_20260923b.json")
kept = {c["id"]: c for c in json.load(open(os.path.join(SCRATCH, "eu_kept.json")))}

GATE = "gate exit 0 -> 'OK {cc} (tier1): sponsorship not stated in the posting " \
       "(allowed: she states that she needs support for a work permit) | manual hand-off: " \
       "NOT allowed (NL only)' = sponsor: not stated"

IE_REG = ("Ireland has no public employer sponsor register to check against (unlike the NL IND "
          "recognised-sponsor list), so the evidence is the permit route itself: a non-EEA hire needs "
          "an employment permit from the Department of Enterprise, Trade and Employment (Employment "
          "Permits Act 2006, as amended 2024) and the employer must be Revenue-registered with a "
          "2-year+ offer; data-engineering/ICT roles with specific skills are on the Critical Skills "
          "Occupations List effective 13 May 2026 (SI 213 of 2026) and the reported 2026 Critical "
          "Skills salary threshold is EUR 40,904/yr (= EUR 3,409/month gross), i.e. only just above "
          "the EUR 3,300/month floor - verify the current threshold on enterprise.gov.ie before "
          "relying on it. The posting does not state sponsorship either way, so this must be raised "
          "in the first call, never assumed.")
DE_REG = ("Germany has no employer sponsor register either: a non-EEA hire is made through the "
          "employer-supported EU Blue Card / skilled-worker residence title (AufenthG s.18b), which "
          "needs a concrete offer and the employer's paperwork, so the route is employer-dependent by "
          "definition. The posting does not state sponsorship or work-permit support either way.")
PERMIT = ("Candidate holds a Dutch highly-skilled-migrant (HSM) permit valid to 3 Dec 2026 - it is "
          "NL-only and confers no local work rights anywhere else, so the application must say "
          "plainly 'Dutch HSM permit to 3 Dec 2026; I would need your support for an Irish employment "
          "permit / a German Blue Card, and I am open to relocating'.")

ROLES = [
    dict(
        slug="intact-insurance-ie-data-engineer",
        company="Intact Insurance Ireland DAC",
        role="Data Engineer",
        location="Dundrum, Dublin 16, Ireland (hybrid)",
        country="IE",
        fit=5.0,
        apply_url="https://careers.rsagroup.ie/jobs/view/2921",
        jd_path="discovery/jd-eu-20260923/intact-insurance-ie-data-engineer.md",
        notes=(
            "FRESHNESS: LinkedIn guest card 2026-09-07 (16 days at the 2026-09-23 sweep) and the "
            "employer's own vacancy list still carries req 2921 as 'Data Engineer | Dundrum - Dublin "
            "16' (careers.rsagroup.ie/jobs/view/2921 verified HTTP 200 live on 2026-09-23). "
            + GATE.format(cc="IE") + ". " + IE_REG + " " + PERMIT + " "
            "WHY IT FITS A MID-LEVEL DATA/INTEGRATION ENGINEER (fit 5.0, the best stack match in the "
            "sweep): the JD asks for 3-5 years, i.e. exactly his band; Microsoft SQL Server + SSMS + "
            "SSRS + SSIS alongside ETL development and data integration, data-warehousing concepts, "
            "'Advanced SQL and Data Bricks experience is compulsory', Power BI, exposure to Azure Data "
            "Services (Azure SQL) and Python - this is his production toolchain almost item for item "
            "(704-process SQL Server/SSIS ETL estate, performance tuning, zero-break audit, Azure/"
            "Databricks, Power BI). Reporting line is the Head of DataOps in a hub-and-spoke team. "
            "GAPS TO DISCLOSE HONESTLY: SAS (Base/EG SAS) is a core requirement he has no production "
            "record for - frame the SSIS/SQL Server migrations as the transferable part and commit to "
            "fast SAS ramp-up; SSRS report building is adjacent rather than deep; the insurance "
            "regulatory (Central Bank Fitness & Probity / controlled function) context is new. "
            "OWN APPLY URL RESOLVED (not a LinkedIn mirror): Intact Insurance Ireland's own careers "
            "page links to the RSA/Intact group vacancy portal careers.rsagroup.ie, where the req is "
            "job 2921; the LinkedIn card is id 4464349772. Tracker check: 'Intact' has 0 hits among "
            "the 282 rows of build_tracker.py. Salary rule: no gross figure is stated in the posting, "
            "so nothing falls at or below EUR 3,300/month. Note he must NOT keyword-inflate SAS or the "
            "Spark side; lead with the ETL/SSIS/SQL Server outcomes."),
    ),
    dict(
        slug="doit-data-engineer-cloud-saas-integrations",
        company="DoiT International Ltd (DoiT)",
        role="Data Engineer - Cloud & SaaS Integrations",
        location="Remote EMEA - employed in Ireland (also UK, Estonia, NL, Sweden, Israel)",
        country="IE",
        fit=4.5,
        apply_url="https://job-boards.greenhouse.io/doitintl/jobs/7990925003",
        jd_path="discovery/jd-eu-20260923/doit-data-engineer-cloud-saas-integrations.md",
        notes=(
            "FRESHNESS: LinkedIn guest card 2026-09-11 (12 days); the employer's own Greenhouse req "
            "7990925003 is live (HTTP 200 on 2026-09-23) and states the location set as 'UK, Ireland, "
            "Estonia, the Netherlands, Sweden and Israel'. " + GATE.format(cc="IE") + ". " + IE_REG +
            " " + PERMIT + " WHY IT FITS A MID-LEVEL DATA/INTEGRATION ENGINEER (fit 4.5): the title "
            "is literally integrations work - build and maintain integrations against third-party "
            "billing/usage REST APIs, own orchestration/scheduling/backfills, normalise dozens of "
            "vendor shapes, and hold data-correctness/reconciliation standards. Requirements are 3+ "
            "years with production pipeline ownership (his band), strong SQL with query-performance "
            "reasoning, Python, an orchestration framework (Airflow/Dagster preferred, dbt explicitly "
            "counted as relevant), a cloud warehouse (Snowflake/BigQuery/Redshift) and REST-API "
            "integration realities (pagination, rate limits, partial failures, restatements). His "
            "API/ETL integration work, Snowflake performance work and reconciliation/audit habits map "
            "directly, and the 'AI-augmented working style' requirement is a genuine differentiator: "
            "he ships RAG/agent pipelines and uses AI tooling daily. GAPS TO DISCLOSE: Dagster is new "
            "to him (Airflow-adjacent understanding only), ClickHouse/FinOps and cloud-billing "
            "(AWS/GCP/Azure cost exports, FOCUS) domain knowledge are absent, Go is not in his stack, "
            "and the 'unlimited vacation / remote-first' culture expects high autonomy. OWN APPLY URL "
            "RESOLVED (not a LinkedIn mirror): DoiT's own Greenhouse board, job 7990925003, "
            "greenhouse listing 'Data Engineer - Cloud & SaaS Integrations, Remote EMEA'. Tracker "
            "check: 'DoiT' has 0 hits among the 282 build_tracker.py rows. Salary rule: no gross "
            "figure stated, so nothing falls at or below EUR 3,300/month. LinkedIn card id 4463975389."),
    ),
    dict(
        slug="version-1-data-engineer-microsoft-fabric",
        company="Version 1",
        role="Data Engineer - Microsoft Fabric (Public Sector & Utilities, Ireland)",
        location="Dublin, Ireland (hybrid)",
        country="IE",
        fit=4.0,
        apply_url="https://version1.com/en-us/careers/job-listing/data-engineer-microsoft-fabric-ref6496s",
        jd_path="discovery/jd-eu-20260923/version-1-data-engineer-microsoft-fabric.md",
        notes=(
            "FRESHNESS: LinkedIn guest card 2026-09-17 (6 days); the employer's own board req "
            "ref6496s is live (HTTP 200 on 2026-09-23) and the same req on Version 1's own "
            "SmartRecruiters ATS (jobs.smartrecruiters.com/Version1/744000131483999) still carries "
            "the stated band 'Compensation: EUR 50000 - EUR 65000 - yearly', i.e. EUR 4,167-5,417/"
            "month gross - well above the EUR 3,300/month floor, and above the reported 2026 Critical "
            "Skills threshold of EUR 40,904. " + GATE.format(cc="IE") + ". " + IE_REG + " " + PERMIT +
            " WHY IT FITS A MID-LEVEL DATA/INTEGRATION ENGINEER (fit 4.0): a Microsoft-partner "
            "consultancy modernising an analytics platform from Oracle into Microsoft Fabric - the "
            "work is pipeline design/development, metadata-driven ingestion and orchestration, "
            "integration testing for data quality/stability, data modelling for analytics and "
            "reporting, and semantic-model lift-and-shift. Version 1 lists the role at LinkedIn's "
            "'Mid-Senior level'. His Azure/SQL Server/Power BI/semantic-layer and pipeline work makes "
            "him competitive, and 'integration testing to support data quality and system stability' "
            "is exactly his audit/reconciliation strength. GAPS TO DISCLOSE: hands-on Microsoft Fabric "
            "is listed as ESSENTIAL and he has not shipped Fabric in production (he has ADF/Azure SQL/"
            "Power BI - say 'conceptual Fabric knowledge, no production Fabric'); Microsoft Purview "
            "scanning/cataloguing and Oracle are not in his production record either. OWN APPLY URL "
            "RESOLVED (not a LinkedIn mirror): version1.com careers job ref6496s (Dublin, Hybrid, "
            "Public Sector & Utilities Ireland); LinkedIn card id 4466286298. Tracker check: "
            "'Version 1' / 'Version1' have 0 hits among the 282 build_tracker.py rows. Salary rule "
            "satisfied by the stated EUR 50-65k band."),
    ),
    dict(
        slug="primer-data-engineer-iii",
        company="Primer (Primer.io)",
        role="Data Engineer III",
        location="Remote-first, employed in Ireland (also UK, Hungary, Poland, Portugal, Romania, South Africa)",
        country="IE",
        fit=4.0,
        apply_url="https://jobs.ashbyhq.com/primer.io/49e633ec-f5de-42f1-8db9-6a6ea86142bf",
        jd_path="discovery/jd-eu-20260923/primer-data-engineer-iii.md",
        notes=(
            "FRESHNESS: LinkedIn guest card 2026-09-14 (9 days); the employer's own Ashby board "
            "(jobs.ashbyhq.com/primer.io) lists 'Data Engineer III' for United Kingdom; Hungary; "
            "Ireland; Poland; Portugal; Romania; South Africa, remote, and the req page is live "
            "(HTTP 200 on 2026-09-23) with 'Published: 2026-08-07' on the UK mirror of the same req "
            "id - both dates are inside the one-month window. " + GATE.format(cc="IE") + ". " + IE_REG
            + " " + PERMIT + " WHY IT FITS A MID-LEVEL DATA/INTEGRATION ENGINEER (fit 4.0): Primer is "
            "a payments-infrastructure company and 'Data Engineer III' is their mid band; the JD asks "
            "for Python + SQL, batch/streaming pipeline building and maintenance, Snowflake as the "
            "warehouse, dbt for transformations, CDC pipelines, internal tools/APIs for analytics, "
            "product and ML, and CI/CD + automated testing as a discipline. His Snowflake depth, "
            "SQL/ETL work, API integrations and test/audit habits are the match, and the payments/ "
            "financial-correctness domain rewards his reconciliation instinct. GAPS TO DISCLOSE: dbt "
            "is conceptual/POC for him rather than production; CockroachDB/DynamoDB/Elasticsearch, "
            "Kubernetes+Helm and Terraform are outside his production record; the role is explicitly "
            "remote-first with no QA function, so testing and self-direction are on the engineer. OWN "
            "APPLY URL RESOLVED (not a LinkedIn mirror): Primer's own Ashby board req "
            "49e633ec-f5de-42f1-8db9-6a6ea86142bf (their board lists Ireland as an eligible country). "
            "Tracker check: 'Primer' has 0 hits among the 282 build_tracker.py rows. Salary rule: no "
            "gross figure stated (only 'competitive share options'), so nothing falls at or below EUR "
            "3,300/month. LinkedIn card id 4455295221."),
    ),
    dict(
        slug="cityswift-analytics-engineer",
        company="CitySwift",
        role="Analytics Engineer",
        location="Galway, Ireland (hybrid, core hours 10-16)",
        country="IE",
        fit=4.0,
        apply_url="https://cityswift.com/job-post/?gh_jid=7762442003",
        jd_path="discovery/jd-eu-20260923/cityswift-analytics-engineer.md",
        notes=(
            "FRESHNESS: LinkedIn guest card 2026-09-17 (6 days); the employer's own Greenhouse board "
            "behind cityswift.com/careers shows 'Analytics Engineer - Galway Ireland' with "
            "updated_at 2026-09-08 (gh_jid=7762442003, live HTTP 200 on 2026-09-23) - both inside the "
            "one-month window (an older July 2026 aggregator repost of the same title exists and was "
            "ignored in favour of the employer's board). " + GATE.format(cc="IE") + ". " + IE_REG + " "
            + PERMIT + " WHY IT FITS A MID-LEVEL DATA/INTEGRATION ENGINEER (fit 4.0): the ask is 3+ "
            "years in a data-centric role (exactly his band), advanced SQL (window functions, CTEs, "
            "optimisation), deep familiarity with a cloud warehouse (Snowflake/Redshift/BigQuery - he "
            "has production Snowflake including a ~25% query-performance win), data modelling that "
            "follows team conventions, Git workflows/PR review, semantic-layer views powering "
            "customer-facing analytics and AI tools, and scalable dashboards. His semantic-layer, "
            "Power BI and modelling work plus the AI/RAG experience line up with 'the centre of AI "
            "adoption'; the level is deliberately mid and the JD says it seeks support from senior "
            "colleagues rather than leading. GAPS TO DISCLOSE: BigQuery is not in his stack, the "
            "transport-network domain is new, and analytics engineering is a lane away from pure "
            "pipeline engineering, so the letter must lead with modelling/semantic work, not Spark. "
            "OWN APPLY URL RESOLVED (not a LinkedIn mirror): CitySwift's own Greenhouse req via "
            "cityswift.com/job-post/?gh_jid=7762442003. Tracker check: 'CitySwift' has 0 hits among "
            "the 282 build_tracker.py rows. Salary rule: no gross figure stated (only a EUR 4,000 "
            "referral reward), so nothing falls at or below EUR 3,300/month. LinkedIn card id "
            "4468612043."),
    ),
    dict(
        slug="sandbox-interactive-data-engineer",
        company="Sandbox Interactive (Stillfront Group)",
        role="Data Engineer (m/f/d)",
        location="Berlin, Germany (hybrid, Prenzlauer Berg)",
        country="DE",
        fit=3.5,
        apply_url="https://sandboxinteractive.teamtailor.com/jobs/8316016-data-engineer-m-f-d",
        jd_path="discovery/jd-eu-20260923/sandbox-interactive-data-engineer.md",
        notes=(
            "FRESHNESS: LinkedIn guest card 2026-09-03 (20 days); the employer's own Teamtailor req "
            "8316016 is live (HTTP 200 on 2026-09-23) and a third-party tracker dates the post "
            "2026-09-03 - inside the one-month window. ENGLISH-FIRST: the German-language rule does "
            "not fire - the JD body is written in English and its only language requirement is "
            "'Excellent communication skills (presentation, verbal and written) in English'; there is "
            "no German-fluency line anywhere in the text, and the employer offers company-sponsored "
            "language courses. " + GATE.format(cc="DE") + ". " + DE_REG + " " + PERMIT + " "
            "WHY IT FITS A MID-LEVEL DATA/INTEGRATION ENGINEER (fit 3.5): the bar is 3+ years as a "
            "Data Engineer, SQL proficiency with query optimisation, Python/C# or similar, scalable "
            "pipeline/ETL building, relational and NoSQL understanding, BI/visualisation tooling "
            "(Power BI is named) and data modelling/warehousing concepts - a clean mid-level match to "
            "his SQL Server/SSIS/ETL + Power BI core. It is the ONLY German posting in this sweep "
            "whose JD is both English-written and free of a German-fluency requirement, so it is "
            "carried for DE coverage. GAPS TO DISCLOSE: the domain is live-game analytics (ELK stack "
            "and Cassandra are preferred, not required), no cloud warehouse is named so his "
            "Azure/Databricks/Snowflake depth is a bonus rather than a requirement, and the employer's "
            "own board lists the employment type as TEMPORARY - a fixed-term German contract is a "
            "real complication for a Blue Card and must be asked about in the first call. NO SALARY "
            "STATED, so nothing falls at or below EUR 3,300/month. Tracker check: 'Sandbox' has 0 hits "
            "among the 282 build_tracker.py rows. LinkedIn card id 4461906199."),
    ),
]

rows = []
for r in ROLES:
    c = kept[r["slug"] and None] if False else None
    rows.append(r)

# attach kw from the sweep cards
IDMAP = {"intact-insurance-ie-data-engineer": "4464349772",
         "doit-data-engineer-cloud-saas-integrations": "4463975389",
         "version-1-data-engineer-microsoft-fabric": "4466286298",
         "primer-data-engineer-iii": "4455295221",
         "cityswift-analytics-engineer": "4468612043",
         "sandbox-interactive-data-engineer": "4461906199"}
for r in ROLES:
    jid = IDMAP[r["slug"]]
    card = kept.get(jid, {})
    kws = card.get("kws") or [card.get("kw", "")]
    r["kw"] = ", ".join([k for k in kws if k])
    r["_linkedin_id"] = jid
    r["_card_posted"] = card.get("posted", "")
    r["_card_company"] = card.get("company", "")
    r["_card_location"] = card.get("location", "")
    r["_card_url"] = card.get("url", "")
    for k in ["slug", "company", "role", "location", "country", "fit", "apply_url", "kw",
              "jd_path", "notes"]:
        assert r.get(k) not in (None, ""), (r["slug"], k)

order = ["slug", "company", "role", "location", "country", "fit", "apply_url", "kw", "jd_path",
         "notes"]
out = []
for r in ROLES:
    out.append({k: r[k] for k in order})
with open(OUT, "w") as fh:
    json.dump(out, fh, indent=1)
    fh.write("\n")
print("WROTE", OUT, len(out), "roles")
for r in out:
    print("  %-5s %-3s %s | %s" % (r["fit"], r["country"], r["company"], r["role"]))
# sanity: every jd_path exists
for r in out:
    p = os.path.join(WS, r["jd_path"])
    print(("JD-OK  " if os.path.exists(p) else "JD-MISS"), r["jd_path"], os.path.getsize(p) if os.path.exists(p) else "-")
