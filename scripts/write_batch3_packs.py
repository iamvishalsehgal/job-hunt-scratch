#!/usr/bin/env python3
"""Write fit.md + apply-url.txt for the four hard-skip roles of pack batch 3."""
import os

ROOT = "/home/ubuntu/.hermes/profiles/vishal/workspace/applications/"
APPLY = {
 "dustin-data-engineer": "https://jobs.dustin.com/jobs/8102002-data-engineer",
 "ilionx-data-analytics-engineer": "https://werkenbij.ilionx.com/vacatures/data-analytics-engineer-5148924",
 "athora-netherlands-azure-data-platform-engineer": "https://athora.nl/en/working-at-athora",
 "cegeka-data-engineer-snowflake": "https://www.cegeka.com/nl-nl/werkenbij/vacatures/data-engineer-snowflake-8276",
}
FIT = {
"dustin-data-engineer": """# Fit - Dustin Netherlands B.V., Data Engineer (Arnhem / Nijmegen, hybrid)

Score: 3.8 / 5 technical - HARD SKIP, employer refuses permit support.

- Technical fit is real: Azure data platform work, Databricks, CI/CD and SQL/Python map onto his Azure
  Fabric migration (704 ETL processes audited, 0 breaks), Azure APIM/Functions and PySpark work; the only
  stated gap is Terraform in production (his infrastructure work is Azure-native so far, alongside CI/CD).
- HARD SKIP rule 4(b), no visa sponsorship: the posting body itself says "Please note that for this specific
  job, we dont provide any relocation or work permit sponsorship support." Captured in
  applications/dustin-data-engineer/jd.md line 37 from the LinkedIn posting, and confirmed live on Dustin's
  own board jobs.dustin.com/jobs/8102002-data-engineer on 2026-09-23. He holds an HSM permit that needs an
  IND-recognized sponsor for the transfer, so this posting cannot employ him.
- Employer check: Dustin Netherlands B.V. is on the IND register (data/register_names.txt), so the register
  is not the blocker; the employer's own policy line is. gates/dutch_gate.py returns exit 0 (no Dutch gate
  hit), so language is not the blocker either.
- No CV, cover letter, portal attempt or email spent. Dustin also states that it does not accept cover letters.
""",
"ilionx-data-analytics-engineer": """# Fit - IlionX Group B.V., Data Analytics Engineer (Zwolle and other NL offices)

Score: 4.0 / 5 technical - HARD SKIP on explicit Dutch fluency.

- Technical fit is strong: Azure Fabric, Data Factory, Synapse, data lakehouse, Power BI/Tabular models,
  DAX, M-query and dimensional modelling are his daily stack (Fabric migration track, SQL Server Data
  Vault 2.0, Power BI with advanced DAX), and the posting's consulting and coaching element matches his
  co-lead role on the Van den Bosch connectivity track.
- HARD SKIP rule 4(a): the posting requires "Je hebt een uitstekende beheersing van de Nederlandse taal in
  woord en geschrift" (excellent command of Dutch, spoken and written). gates/dutch_gate.py returns exit 10
  SKIP_DUTCH_FLUENCY on the captured posting (applications/ilionx-data-analytics-engineer/jd.md), and the
  same line is live on ilionx's own board werkenbij.ilionx.com/vacatures/data-analytics-engineer-5148924
  (verified 2026-09-23).
- Salary is not the blocker: the own board states EUR 4.500 to EUR 6.500 gross per 40 hours plus bonus,
  above both the EUR 3.300 floor and the EUR 4.000 ask. Employer check: IlionX Group B.V. is on the IND
  register (data/register_names.txt).
- No CV, cover letter, portal attempt or email spent.
""",
"athora-netherlands-azure-data-platform-engineer": """# Fit - Athora Netherlands N.V., Azure Data Platform Engineer (Amsterdam)

Score: 4.3 / 5 technical - HARD SKIP on explicit Dutch fluency.

- Technical fit is the closest of this batch: Microsoft Azure data platform ownership, Databricks pipelines,
  a well-run Power BI environment, data governance (security, monitoring, compliance), Python, PySpark, SQL
  and CI/CD. His Azure Fabric migration (704 ETL processes audited, 0 breaks), SQL Server Data Vault 2.0
  modelling, Azure APIM/Functions work and Power BI advanced DAX all sit on that list; the stated gaps are
  Terraform (Azure-native infrastructure so far, alongside CI/CD) and Databricks in production.
- HARD SKIP rule 4(a): the posting requires "Vloeiende beheersing van de Nederlandse taal" (fluent command
  of Dutch) and its body is written in Dutch throughout. gates/dutch_gate.py returns exit 10
  SKIP_DUTCH_FLUENCY on the captured posting
  (applications/athora-netherlands-azure-data-platform-engineer/jd.md, captured 2026-09-23). The same
  requirement line appears on four independent board mirrors (bebee, nogigiddy, tsenta, jobleads) and in the
  discovery cache copy, so it is not a scraping artefact.
- Salary is not the blocker: the LinkedIn card states a base pay range of EUR 4,335 to EUR 6,776 per month,
  above both the EUR 3,300 floor and the EUR 4,000 ask. Employer check: Athora Netherlands N.V. is on the
  IND register (data/register_names.txt).
- No CV, cover letter, portal attempt or email spent.
""",
"cegeka-data-engineer-snowflake": """# Fit - Cegeka Nederland, Data Engineer - Snowflake (Veenendaal and other NL offices)

Score: 4.2 / 5 technical - HARD SKIP, posting is in Dutch.

- Technical fit is strong: Snowflake ETL/ELT development in Azure, data warehouse modelling, and pipeline
  quality, monitoring and testing are all on his record (Snowflake ETL with PySpark at Kuehne+Nagel, 25
  percent faster processing; SQL Server Data Vault 2.0 modelling; Azure Fabric migration with 704 ETL
  processes audited, 0 breaks; GitLab CI/CD test work).
- HARD SKIP rule 4(a): the posting is written entirely in Dutch with no English variant.
  gates/dutch_gate.py returns exit 11 SKIP_DUTCH_LANGUAGE (14 Dutch markers, 3.35 per 1k chars) on the
  captured posting (applications/cegeka-data-engineer-snowflake/jd.md), and Cegeka's own board posting
  cegeka.com/nl-nl/werkenbij/vacatures/data-engineer-snowflake-8276 is Dutch throughout (verified live
  2026-09-23).
- Salary is not the blocker: prior capture of the same board shows a band around EUR 5.000 to EUR 6.500,
  above both the EUR 3.300 floor and the EUR 4.000 ask. Employer check: Cegeka Nederland is on the IND
  register (data/register_names.txt line 2002).
- No CV, cover letter, portal attempt or email spent.
""",
}

for slug, body in FIT.items():
    folder = ROOT + slug
    os.makedirs(folder, exist_ok=True)
    for name, text in (("fit.md", body), ("apply-url.txt", APPLY[slug] + "\n")):
        path = os.path.join(folder, name)
        with open(path, "w") as fh:
            fh.write(text)
        print("WROTE %s %d" % (path, os.path.getsize(path)))
