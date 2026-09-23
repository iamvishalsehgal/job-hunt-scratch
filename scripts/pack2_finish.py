"""Pack batch 2 (2026-09-23g): finish the four skipped roles - fit notes + results lines."""
import datetime
import pathlib

WS = pathlib.Path("/home/ubuntu/.hermes/profiles/vishal/workspace")
APPS = WS / "applications"
RUN = WS / "runs" / "2026-09-23g"
NOW = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# --- itility: strengthen the JD capture with the verbatim requirement + gate result ---
it = APPS / "itility-data-engineer" / "jd.md"
add = """
## Verbatim language requirement (own board capture, jd-full.txt)
- "Je bent een teamspeler en beschikt over goede communicatieve vaardigheden in het Nederlands."
- Application form asks: "Hoe vaardig ben je in het Nederlands?" (Niet / Conversatie / Beroepsmatig /
  Moedertaal of tweetalig) - i.e. Dutch proficiency is a scored form field.
- "python3 gates/dutch_gate.py applications/itility-data-engineer/jd-full.txt" -> exit 10 SKIP_DUTCH_FLUENCY.
- The posting body itself is in Dutch, so rule 4(a) applies twice over: language of the posting and an
  explicit Dutch communication requirement. Candidate is Dutch A2-B1. Hard skip, no submission attempted.
"""
it.write_text(it.read_text(encoding="utf-8") + add, encoding="utf-8")

FIT = {}

FIT["itility-data-engineer"] = """# Fit - Itility B.V., Data Engineer (Eindhoven / Randstad, hybrid)

Score: 3.6 / 5 technical - HARD SKIP on language (rule 4(a))

- Technical fit is real: Python and Spark data connectors, validation tests inside the pipeline,
  monitoring and alerting, incident ownership, Azure Data Factory / Fabric or Databricks as a plus,
  Power BI for dashboarding, 2 to 3 years of relevant experience. His current role is the same work
  at a larger estate: 704 ETL processes audited for migration impact with zero reporting breaks,
  Data Vault 2.0 on SQL Server, Azure Fabric / APIM / Functions, monitoring and incident handling.
- HARD SKIP: the posting is in Dutch and its "Dit ben jij" list ends with "Je bent een teamspeler en
  beschikt over goede communicatieve vaardigheden in het Nederlands"; the application form scores
  Dutch proficiency ("Hoe vaardig ben je in het Nederlands?", up to Moedertaal of tweetalig).
  gates/dutch_gate.py on the full own-board capture returns exit 10 SKIP_DUTCH_FLUENCY. He is A2-B1.
- Employer check: Itility B.V. is on the IND register (data/register_names.txt line 5820), so
  sponsorship would not have been the blocker. No salary figure is published on the posting.
- Nothing submitted, no CV or cover letter built, no email sent.
"""

FIT["aurea-imaging-data-engineer"] = """# Fit - Aurea Imaging B.V., Data Engineer (Utrecht, hybrid, 3 days office)

Score: 3.2 / 5 technical - HARD SKIP on work rights (rule 4(b))

- Technical fit is partial: Python (FastAPI), PostgreSQL and MongoDB, Kubernetes-based cloud
  infrastructure, Apache Iceberg, MLOps tooling (ClearML, FiftyOne, CVAT), plus productionising models.
  His strength is the adjacent side: PySpark and Spark Structured Streaming, Kafka, Snowflake,
  Data Vault modelling, Azure and GCP, and an MSc thesis on LLM plus knowledge-graph pipelines. The
  posting is genuinely a geospatial / GeoAI role: geospatial data, GIS, remote sensing and edge
  devices (Kairos, Nvidia Jetpack) are the day-to-day, which is not his area.
- HARD SKIP: the posting states verbatim "Candidates must already have the right to work in the
  Netherlands. Visa sponsorship is not available for this position." An HSM transfer needs an
  IND-recognised sponsor, so the role is unusable. gates/eu_scope_gate.py check --country NL returns
  exit 10 on it. Aurea Imaging B.V. is on the IND register (line 967), but the vacancy itself refuses
  sponsorship.
- Dutch is not an issue here (English-language posting, gate exit 0).
- Nothing submitted, no CV or cover letter built, no email sent.
"""

FIT["datacation-data-engineer"] = """# Fit - Datacation B.V., Data Engineer (Eindhoven / Amsterdam)

Score: 3.7 / 5 technical - HARD SKIP on language (rule 4(a))

- Technical fit is strong: at least 2 years in data engineering and cloud, batch and streaming
  pipelines in Azure, Databricks plus PySpark, Azure Data Factory, Data Lake and medallion
  architecture, Docker and CI/CD (GitHub Actions), SQL and data modelling, MSc in a relevant field.
  That is close to his current stack (Azure Fabric, Data Factory, APIM, PySpark, Data Vault 2.0) and
  his MSc (TU/e plus Tilburg, JADS).
- HARD SKIP: the own-board card (datacation.nl/careers/data-engineer, live 2026-09-23) lists
  "Excellent command of the Dutch language, both spoken and written", and the LinkedIn posting is
  published in Dutch with "Uitstekende beheersing van de Nederlandse taal in woord en geschrift".
  gates/dutch_gate.py on the capture returns exit 10 SKIP_DUTCH_FLUENCY. He is Dutch A2-B1.
- Employer check: Datacation B.V. is on the IND register (line 2755), so sponsorship would not have
  been the blocker. No salary published on either card.
- Nothing submitted, no CV or cover letter built, no email sent.
"""

FIT["alfen-data-engineer"] = """# Fit - Alfen B.V., Data Engineer (Almere)

Score: 3.9 / 5 technical - HARD SKIP on language (rule 4(a))

- Strong technical overlap: build and maintain pipelines across operational and analytical platforms;
  Microsoft SQL Server (T-SQL, stored procedures, ETL/ELT); dimensional modelling and data warehouse
  best practice; data quality through validation, monitoring and lineage; Power BI and DAX; Snowflake
  and Matillion; Azure infrastructure; releases and migrations. His SQL Server and Data Vault 2.0 work,
  the 704-process ETL audit with zero reporting breaks and the Power BI / DAX layer map onto it directly.
- HARD SKIP: the own-board vacancy (alfen.com, live 2026-09-23) requires "Strong communication skills
  in English and Dutch" (NL version: "goede beheersing van Nederlands en Engels, mondeling en
  schriftelijk"). gates/dutch_gate.py returns exit 10 SKIP_DUTCH_FLUENCY. He is Dutch A2-B1.
- Other honest gaps: the posting asks 5+ years IT with 3+ years data-focused; Snowflake and Matillion
  experience is listed as a strong plus and his Snowflake exposure is from the Kuehne+Nagel internship.
  Alfen B.V. is on the IND register (lines 445-446), so sponsorship would not have been the blocker.
- Nothing submitted, no CV or cover letter built, no email sent.
"""

ROWS = [
    ("itility-data-engineer",
     "skipped",
     "careers.itility.nl/o/data-engineer live 2026-09-23; dutch_gate exit 10 SKIP_DUTCH_FLUENCY on full capture",
     "Posting in Dutch; \"goede communicatieve vaardigheden in het Nederlands\" plus a scored Dutch-proficiency form field. Rule 4(a) hard skip, no submission. IND sponsor Itility B.V. on register; no salary published.",
     "own-board-verified hard skip (Dutch): SKIP_DUTCH_FLUENCY",
     "https://nl.linkedin.com/jobs/view/data-engineer-at-itility-4431123040"),
    ("aurea-imaging-data-engineer",
     "skipped",
     "JD verbatim: \"Candidates must already have the right to work in the Netherlands. Visa sponsorship is not available\"; eu_scope_gate exit 10",
     "HARD SKIP rule 4(b): HSM transfer needs an IND-recognised sponsor and the posting refuses sponsorship. IND Aurea Imaging B.V. on register; English posting, dutch_gate exit 0. No CV/letter spent.",
     "hard skip (no visa sponsor), LinkedIn guest view mirrored on qarera/inClimate",
     "https://nl.linkedin.com/jobs/view/data-engineer-at-aurea-imaging-4469145261"),
    ("datacation-data-engineer",
     "skipped",
     "own board datacation.nl/careers/data-engineer: \"Excellent command of the Dutch language, both spoken and written\"; dutch_gate exit 10",
     "HARD SKIP rule 4(a) Dutch fluency; LinkedIn posting also Dutch. IND Datacation B.V. on register (line 2755), no salary published, own board full-time card live. No submission, no CV/letter.",
     "own-board-verified hard skip (Dutch): SKIP_DUTCH_FLUENCY",
     "https://nl.linkedin.com/jobs/view/data-engineer-at-datacation-4458169188"),
    ("alfen-data-engineer",
     "skipped",
     "own board alfen.com vacancy page: \"Strong communication skills in English and Dutch\"; dutch_gate exit 10",
     "HARD SKIP rule 4(a) Dutch required alongside English. IND Alfen B.V. on register; 5+ yrs and Snowflake/Matillion also asked. No salary published. No submission, no CV/letter built.",
     "own-board-verified hard skip (Dutch): SKIP_DUTCH_FLUENCY",
     "https://nl.linkedin.com/jobs/view/data-engineer-at-alfen-4446339385"),
]

written = []
for slug, text in FIT.items():
    p = APPS / slug / "fit.md"
    p.write_text(text, encoding="utf-8")
    assert "\u2014" not in text and "\u2013" not in text, slug
    written.append(p)

lines = []
for slug, outcome, evidence, note, route, url in ROWS:
    jd = APPS / slug / "jd.md"
    atts = f"{jd},{APPS / slug / 'fit.md'}"
    lines.append("\t".join([slug, outcome, evidence, note, atts, str(jd), url, route, NOW]))

with open(RUN / "results.tsv", "a", encoding="utf-8") as fh:
    for line in lines:
        fh.write(line + "\n")

print("appended", len(lines), "rows at", NOW)
for p in written:
    print("WROTE", p, p.stat().st_size)
for slug, *_ in ROWS:
    for name in ("jd.md", "jd-full.txt", "fit.md"):
        p = APPS / slug / name
        if p.exists():
            print("WROTE", p, p.stat().st_size)
