#!/usr/bin/env python3
"""Build the missing pack files for batch 3 (Landal full pack, IFS email draft)."""
import json
import os

BASE = "/home/ubuntu/Desktop/job-hunt/applications"

SIG = """
Kind regards,
Vishal Sehgal
vishalsehgal414@gmail.com | +31 6 10159758 | linkedin.com/in/iamvishalsehgal
"""

# ---------------------------------------------------------------- Landal
landal = os.path.join(BASE, "landal-greenparks-data-analyst")
os.makedirs(landal, exist_ok=True)

tailoring = {
    "headline": "Vishal Sehgal",
    "summary": (
        "Analytics and data engineer with an MSc in Data Science (TU/e with Tilburg University, JADS, "
        "November 2025), based in 's-Hertogenbosch and open to Amsterdam. My daily work is turning raw "
        "operational data into documented, reliable analytics assets: I co-lead the Connectivity track of an "
        "Azure Fabric migration, model SQL Server data warehouses in Data Vault 2.0, and build Power BI "
        "semantic models and DAX measures for business stakeholders. My MSc thesis built a semantic catalogue "
        "of AI models as an RDF/SPARQL knowledge base in Neo4j over real source data, which is the same "
        "discipline as a governed semantic layer: definitions, lineage and provenance made explicit. "
        "Python, SQL, dbt-style transformations, Azure and GCP are the stack I work in."
    ),
    "skills": [
        {"name": "Analytics Engineering & Semantic Models",
         "entries": "Semantic layers and metric definitions, Power BI models with advanced DAX, dimensional (Kimball) modelling, Data Vault 2.0 (hub/link/satellite), documented and tested transformations, data quality checks and integrity flagging"},
        {"name": "BI & Reporting",
         "entries": "Power BI (advanced DAX, dashboards, business reporting), Excel (advanced models), Plotly and Dash, requirement translation into BI solutions for Finance, Commerce and Operations stakeholders"},
        {"name": "Data Platforms & Pipelines",
         "entries": "SQL transformations and ingestion support across Azure (Fabric, Data Factory, APIM, Functions) and GCP (BigQuery, Pub/Sub, Cloud Run); Databricks not yet in production, delivery so far on Snowflake, Synapse-style SQL warehouses and BigQuery; PySpark and Kafka streaming"},
        {"name": "Databases",
         "entries": "SQL Server (temporal tables, window functions, geospatial), Snowflake, BigQuery, PostgreSQL, Oracle, MySQL"},
        {"name": "Customer & Marketing Analytics",
         "entries": "Customer segmentation (RFM and K-means), survival analysis, topic modelling (BERTopic), KPI and metric definition for stakeholders; multi-touch attribution and MMM not yet in a production role"},
        {"name": "Engineering Practice",
         "entries": "Git and GitLab CI/CD, Azure DevOps pipelines, Docker, version control and documentation standards, Scrum and JIRA"},
        {"name": "Languages & Tooling",
         "entries": "Python, SQL, R, ASP; RDF/SPARQL and Neo4j for semantic modelling, LangChain, REST and microservices"},
    ],
    "projects": [
        {"name": "Semantic Cataloging with LLMs and Knowledge Graphs (MSc thesis)",
         "desc": "RDF/SPARQL knowledge base in Neo4j over real source data (Hugging Face model cards), with four provenance and attribution methods benchmarked: governed definitions and lineage, not free text"},
        {"name": "SQL Server data warehouse and Data Vault 2.0 models",
         "desc": "Hub/link/satellite modelling, temporal tables, window functions and geospatial logic on production order and master data"},
        {"name": "704-process ETL audit ahead of an Azure Fabric migration",
         "desc": "Code-impact assessment across the estate: zero breaks at cut-over, one at-risk query fixed before go-live"},
        {"name": "Comfy Data Analytics",
         "desc": "2.6M transactions: RFM and K-means customer segmentation plus survival analysis for retention insight"},
        {"name": "Real-time BI dashboard suite (Veena Boutique)",
         "desc": "Daily sales, stock turnover and margin dashboards on SQL Server that gave the owner first visibility into performance"},
    ],
}

letter = """Vishal Sehgal
Uilenburg 5G, 5211 EV 's-Hertogenbosch, Netherlands
vishalsehgal414@gmail.com | +31 6 10159758
linkedin.com/in/iamvishalsehgal | github.com/iamvishalsehgal

Dear Hiring Manager,

I would like to apply for the Data Analyst / Analytics Engineer role at Landal GreenParks in Amsterdam.

Your posting puts DBT models in Databricks, Power BI semantic models and metric definitions at the centre of the role, together with SQL transformation work and close partnership with Data Engineers. That is the work I do today. At Van den Bosch Transporten I co-lead the Connectivity track of an Azure Fabric migration and model SQL Server data in Data Vault 2.0 (hub, link, satellite) with temporal tables and window functions, and I audited 704 ETL processes for code impact before cut-over: zero breaks, one at-risk query fixed. Business-facing reporting is mine as well: a real-time BI dashboard suite on SQL Server gave a ten-person operation its first daily visibility into sales, stock turnover and margin. My MSc thesis (TU/e with Tilburg University, JADS) built a semantic catalogue as an RDF/SPARQL knowledge base in Neo4j over real source data, with four provenance and attribution methods benchmarked, which is the discipline your semantic layer and Customer 360 work asks for.

On the tools: Power BI with advanced DAX, SQL, Python and Azure (Fabric, Data Factory) are my production stack, and I have built PySpark and Kafka pipelines at Kuehne+Nagel (25 percent faster processing, 30 percent lower latency). Databricks and multi-touch attribution are not yet in a production role for me; I work the equivalent problems on Snowflake, BigQuery and Azure today and would pick up Databricks quickly.

I am available from 4 December 2026. My current role is a fixed seven-month contract, 4 May to 3 December 2026, ending by its own terms, and my Highly Skilled Migrant permit runs to 3 December 2026, so Landal GreenParks B.V. would be my IND recognised sponsor. I am open to working from Amsterdam and can be in the office as often as the team needs.

Kind regards,
Vishal Sehgal
"""

fit = """# Fit - Data Analyst / Analytics Engineer, Landal GreenParks B.V. (Amsterdam) - 3.5/5

Verdict: apply. No hard skip: the posting is in English, salary is not stated (so no salary filter hit), Landal
GreenParks B.V. is on the IND register (data/register_names.txt), and it is direct employment, not agency or ZZP.

Justification
1. The core of the role (dbt models, Power BI semantic models and metric definitions, SQL transformations, Data
   Engineer collaboration) maps onto his current job: Azure Fabric migration, SQL Server modelling in Data Vault
   2.0 (hub/link/satellite, temporal tables, window functions), Power BI with advanced DAX, and a 704-process ETL
   code-impact audit that closed with zero breaks.
2. Semantic and modelling discipline is his strongest differentiator: the MSc thesis built a semantic catalogue as
   an RDF/SPARQL knowledge base in Neo4j over real source data with four provenance and attribution methods
   benchmarked - the same governed-definitions thinking a Customer 360 semantic layer needs.
3. Stakeholder-facing analytics is evidenced, not claimed: a real-time BI dashboard suite on SQL Server gave a
   ten-person operation its first daily visibility into sales, stock turnover and margin, plus RFM/K-means
   segmentation and survival analysis on 2.6M transactions.

Blockers / risks
- Databricks: not yet in production for him (Snowflake, BigQuery, Azure Fabric instead); stated plainly.
- Multi-touch attribution (MTA) and MMM: no production experience; adjacent work is segmentation, topic modelling
  and KPI definition. Not hidden in the letter.
- The posting asks a minimum of 2 years as Data Analyst / Analytics Engineer; he exceeds that across his current
  role, Kuehne+Nagel and Veena Boutique. Years thresholds are not a skip reason regardless.
- Salary not posted; the ask stands at EUR 4,400-5,000 gross per month base and must be raised in the first call.
- HSM permit to 3 Dec 2026: the employer must be an IND-recognized sponsor, which Landal GreenParks B.V. is.
- Route: Workday tenant roompot.wd103 (Landal), which PACK_RULES section 8 lists as account-gated; the email route
  bounced earlier in this sweep, so the portal is the only route.
"""

email_md = """# Fallback application email - HELD, do not send

Route: Workday tenant roompot.wd103 (Landal) - account plus email verification, driven as an AUTO apply.
The email route for this role bounced earlier in this sweep, so no address is used. This draft exists only to
satisfy the pack shape and is NOT sent.

Subject: Application: Data Analyst / Analytics Engineer - Vishal Sehgal

To: none-found (previous email route to Landal bounced; portal only)

Dear Landal team,

I would like to apply for the Data Analyst / Analytics Engineer role at your Amsterdam head office. I work as a
Data and Integration Engineer at Van den Bosch Transporten, where I co-lead the Connectivity track of an Azure
Fabric migration, model SQL Server data in Data Vault 2.0 and audit ETL processes for code impact (704 processes,
zero breaks at cut-over). Power BI with advanced DAX, SQL and Python on Azure are my daily tools, and my MSc
thesis built a semantic catalogue as an RDF/SPARQL knowledge base in Neo4j over real source data.

My current role is a fixed seven-month contract, 4 May to 3 December 2026, ending by its own terms, and my HSM
residence permit runs to 3 December 2026, so a new employer needs to be an IND-recognized sponsor; Landal
GreenParks B.V. is on that register. I am available from 4 December 2026.

Attached: cv.pdf and cover-letter.pdf.

Kind regards,
Vishal Sehgal
vishalsehgal414@gmail.com | +31 6 10159758 | linkedin.com/in/iamvishalsehgal
"""

with open(os.path.join(landal, "tailoring.json"), "w") as fh:
    json.dump(tailoring, fh, indent=1, ensure_ascii=False)
with open(os.path.join(landal, "cover-letter.md"), "w") as fh:
    fh.write(letter)
with open(os.path.join(landal, "fit.md"), "w") as fh:
    fh.write(fit)
with open(os.path.join(landal, "email-to-hr.md"), "w") as fh:
    fh.write(email_md)
with open(os.path.join(landal, "apply-url.txt"), "w") as fh:
    fh.write("https://roompot.wd103.myworkdayjobs.com/Landal/job/Headoffice-Amsterdam/Data-Analyst_JR102999\n")

# ---------------------------------------------------------------- IFS email draft
ifs = os.path.join(BASE, "ifs-senior-software-engineer-ai-agents")
ifs_email = """# Fallback application email - HELD, send only if the SmartRecruiters form cannot be driven

Subject: Application: Senior Software Engineer, AI Agents - Vishal Sehgal

To: none-found (SmartRecruiters IFS1 application form is the route; no evidence-bearing IFS recruitment mailbox
was found on ifs.com or the posting, and section 1 forbids a guessed address)

Dear IFS team,

I would like to apply for the Senior Software Engineer, AI Agents role in the Netherlands. At Van den Bosch
Transporten I built the org-wide AI service desk assistant (Copilot Studio with Power Automate flows, around 220
tickets a week) on a 19,084-ticket and 106K-document knowledge base, and I built the retrieval layer under it
myself: a RAG and knowledge-graph pipeline with PII scrubbing, OCR and chunking. The flows read and update records
in the ticketing platform and route work to a person when a rule says a human decides, not only answering
questions. On the gateway side I exposed the COM order API through Azure APIM with Key Vault and subscription-key
authentication and fixed the Seeburger to APIM to Function routing.

My current role is a fixed seven-month contract, 4 May to 3 December 2026, ending by its own terms, and my Highly
Skilled Migrant permit runs to 3 December 2026, so IFS Benelux B.V. would be my IND recognised sponsor. I live in
's-Hertogenbosch and am available from 4 December 2026.

Attached: cv.pdf and cover-letter.pdf.

Kind regards,
Vishal Sehgal
vishalsehgal414@gmail.com | +31 6 10159758 | linkedin.com/in/iamvishalsehgal
"""
with open(os.path.join(ifs, "email-to-hr.md"), "w") as fh:
    fh.write(ifs_email)

# tenure line: keep the automation wording out of every outbound-facing draft
ifs_letter = os.path.join(ifs, "cover-letter.md")
with open(ifs_letter) as fh:
    txt = fh.read()
txt = txt.replace("ending automatically by its own terms", "ending by its own terms")
with open(ifs_letter, "w") as fh:
    fh.write(txt)

print("pack files written")
for d in (landal, ifs):
    print(d, sorted(os.listdir(d)))
