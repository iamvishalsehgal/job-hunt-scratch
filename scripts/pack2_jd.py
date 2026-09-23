"""Pack batch 2 (2026-09-23g): write JD captures for the 4 roles. Verify-only roles."""
import pathlib

WS = pathlib.Path("/home/ubuntu/.hermes/profiles/vishal/workspace")
APPS = WS / "applications"

JD = {}

JD["itility-data-engineer"] = """# JD capture - Data Engineer, Itility B.V. (Eindhoven / Randstad, hybrid)

- apply_url: https://nl.linkedin.com/jobs/view/data-engineer-at-itility-4431123040
- own board: https://careers.itility.nl/o/data-engineer (live 2026-09-23, pulls the same text)
- captured: 2026-09-23 (own board + LinkedIn guest view)
- language: posting is published in Dutch

## Wat ga je doen
- Bouwen van data connectors of verwerkingsoplossingen met Python, Spark of andere programmeertalen.
- Definieren van validatietests binnen de datapijplijn.
- Inrichten van monitoring en alerts, zodat verstoringen of fouten in de datastroom direct zichtbaar zijn.
- Bij incidenten neem jij het voortouw om de oorzaak zo snel mogelijk te achterhalen en op te lossen.
- Samen met het team verantwoordelijk voor bouwen, deployen, onderhouden en optimaliseren van de datastroomoplossing.

## Dit ben jij
- Je hebt een hbo- of wo-diploma.
- Ervaring met Microsoft Azure Data Factory en Fabric of Databricks is een pre.
- Ervaring met datamodelbeheer en dashboarding (bijvoorbeeld met PowerBI) is een pre.
- Je hebt 2 tot 3 jaar relevante werkervaring.
- Goede kennis van SQL, Python en Spark, en basiskennis van datasolutions in containeromgevingen (Kubernetes).
- Je bent een teamspeler en beschikt over goede communicatieve vaardigheden in het Nederlands.

## Terms
- Leaseauto met tankpas of mobiliteitsvergoeding; EUR 115 onkostenvergoeding per maand; 26 vakantiedagen;
  50% ziektekostenbijdrage; 60% pensioenbijdrage; variabele bonus; hybride werken. No salary figure published.
"""

JD["aurea-imaging-data-engineer"] = """# JD capture - Data Engineer, Aurea Imaging B.V. (Utrecht, hybrid, 3 days office)

- apply_url: https://nl.linkedin.com/jobs/view/data-engineer-at-aurea-imaging-4469145261
- captured: 2026-09-23 (LinkedIn guest view, mirrored identically on qarera.com/job/1230562 and
  inclimate.com job page for the same posting id 4469145261)
- language: English posting. Mid-level, 3-5 years.

## Build AI for the future of fruit farming
TreeScout combines sensing, edge computing and AI; unique structured geospatial and agronomic dataset.

## What you'll do
- Develop analytical models for applications in fruit farming.
- Build predictive models; turn proof-of-concepts into scalable, production-ready solutions.
- Build and improve data pipelines and AI workflows.

## Stack
Python-based services (FastAPI), MongoDB, PostgreSQL, Kubernetes-based cloud infrastructure,
Apache Iceberg, TreeScout edge devices (Kairos, Nvidia Jetpack), MLOps with ClearML, FiftyOne, CVAT.

## Working at Aurea (verbatim)
- You will work from our Utrecht office at least three days per week.
- You will join an international team with colleagues from different backgrounds and countries.
- Candidates must already have the right to work in the Netherlands. Visa sponsorship is not
  available for this position.

## Why this is a hard skip
Rule 4(b): the posting states no visa sponsorship and demands existing local work rights. An HSM
transfer (IND recognised sponsor) is the only route open to the candidate, so the role is unusable.
"""

JD["datacation-data-engineer"] = """# JD capture - Data Engineer, Datacation B.V. (Eindhoven / Amsterdam)

- apply_url: https://nl.linkedin.com/jobs/view/data-engineer-at-datacation-4458169188 (posting body in Dutch)
- own board: https://datacation.nl/careers/data-engineer (live 2026-09-23; board lists Data Engineer, full time)
- captured: 2026-09-23 (own board English card + LinkedIn guest view)

## Job description (own board card, English)
- Translating business challenges into scalable, data-driven solutions.
- Independently building, optimizing and maintaining data pipelines (batch and streaming), primarily in Azure.
- Modern data stack: Azure Databricks, PySpark, Azure Data Factory, Azure Data Lake, orchestration tools.
- Data Lake structures such as the medallion architecture (bronze/silver/gold).
- Containerization with Docker and CI/CD pipelines (e.g. GitHub Actions).
- Communicating with clients about project progress and technical decisions; presenting solutions.
- Sharing knowledge with senior data engineers and consultants.

## What do we expect from you?
- Proven experience (at least 2 years) in data engineering, cloud technologies, production pipelines.
- Strong proficiency in Python (PySpark, Pandas, NumPy); solid SQL and data modeling.
- Cloud tooling (preferably Azure): Databricks, Data Lake, Azure Data Factory or Synapse.
- CI/CD, Git, Docker, serverless technologies. MSc or BSc in a relevant field.
- Excellent command of the Dutch language, both spoken and written.
- Pre: consultancy experience; second cloud (AWS/GCP); streaming (Kafka, Event Hubs, Spark Streaming).

## Why this is a hard skip
Rule 4(a): the own-board card states an explicit Dutch-fluency requirement, and the LinkedIn posting is
published in Dutch ("Uitstekende beheersing van de Nederlandse taal in woord en geschrift").
"""

JD["alfen-data-engineer"] = """# JD capture - Data Engineer, Alfen B.V. (Almere)

- apply_url: https://nl.linkedin.com/jobs/view/data-engineer-at-alfen-4446339385
- own board: https://www.alfen.com/en/working-at/vacancies/data-engineer-1275177 (live 2026-09-23)
- captured: 2026-09-23 (own board English vacancy page + LinkedIn guest view)

## What You'll Do
- Design, build and maintain databases and data pipelines across operational systems and the analytical platform.
- Develop and optimise Microsoft SQL Server environments (T-SQL, stored procedures, ETL/ELT pipelines).
- Model data using dimensional modelling and data warehouse best practices.
- Safeguard data quality through validation, monitoring and lineage tracking; monitor performance, resolve incidents.
- Work with Microsoft SQL Server, Matillion, Snowflake, Azure Analysis Services and Power BI.
- Support releases, migrations and ongoing improvements of the data platform; on-call duties when required.

## What You Bring
- Bachelor's or Master's degree in IT, Data, Computer Science or similar.
- 5+ years of experience in IT/technology roles, including 3+ years in data-focused positions.
- Strong expertise in SQL Server (T-SQL, stored procedures).
- Experience with programming languages such as Python, R, C#, Java or similar.
- Hands-on data warehousing, dimensional modelling and ETL/ELT processes.
- Snowflake and Matillion a strong plus; database performance, security and optimisation knowledge.
- Strong communication skills in English and Dutch.

## Why this is a hard skip
Rule 4(a): the posting requires Dutch alongside English (NL version: "goede beheersing van Nederlands
en Engels, mondeling en schriftelijk"). The candidate is Dutch A2-B1, so the role is a hard skip.
"""

for slug, text in JD.items():
    d = APPS / slug
    d.mkdir(parents=True, exist_ok=True)
    p = d / "jd.md"
    p.write_text(text, encoding="utf-8")
    assert "\u2014" not in text and "\u2013" not in text, slug
    print("wrote", p, p.stat().st_size)
