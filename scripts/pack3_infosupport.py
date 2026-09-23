#!/usr/bin/env python3
"""Info Support Senior Data Engineer pack text files (one role, its own tailored CV spec + letter)."""
import json
import pathlib

WS = pathlib.Path("/home/ubuntu/.hermes/profiles/vishal/workspace")
D = WS / "applications" / "info-support-senior-data-engineer"
D.mkdir(parents=True, exist_ok=True)

JD = """# Senior Data Engineer - Info Support (Veenendaal, Data & AI)

Source: https://nl.linkedin.com/jobs/view/senior-data-engineer-at-info-support-4447008381
Own board: https://carriere.infosupport.com/vacatures/senior-data-engineer (SOLLICITEER DIRECT form)
Posted: 1 week ago | 33 applicants | Salary: EUR 4.250 - EUR 5.025 gross per month (40h)
Seniority: Professional | Domain: Data & AI | Location: Nederland (Hybride), HQ Veenendaal

Word omringd door Java Champions, Microsoft MVP's en Data & AI-specialisten. Wij bieden jou onder
andere winstdeling, een leaseauto met internationale tankpas en een onbeperkt opleidingsbudget.

Onze klanten data driven maken. Dat is wat je als Senior Data Engineer doet. Met technieken als
Azure Datafactory, Data Lake, Python, Streaming, Airflow, CI/CD en Databricks draag je bij aan
uitdagingen die grote impact hebben op de maatschappij.

Jouw grote toegevoegde waarde zit in het begrijpen en analyseren van business data requirements om
zo accurate, flexibele en uitbreidbare datamodellen te bouwen. Jouw inzichten en analyses dragen bij
aan de ontwikkelingen van de 21e eeuw; denk aan de veranderingen in de energie-branch door
elektrische auto's en gasloze huizen, digitalisering binnen de zorg en de logistieke uitdagingen
door toenemende online consumptie.

Je ondersteunt hiervoor klanten met deze uitdagingen door hen data driven te laten werken op moderne
data platforms. Je bent in staat moderne data architecturen toe te passen en data warehouses op te
zetten. Zo kunnen data-analyses en rapportages op effectieve wijze uitgevoerd worden. Samen met de
klant zorg jij dat de informatiebehoefte, specifieke wensen en doelen voor het data platform helder
zijn. Je zorgt voor en draagt hands-on bij aan de ontwikkeling, inrichting en implementatie van
datawarehouse-oplossingen. Je begeleidt daarnaast niet alleen klanten, maar ook collega's op het
gebied van data engineering.

Wat bied jij Info Support?
Als ervaren Data Engineer ben je een echte kwartiermaker. Communicatief ben je zeer vaardig. Je
haalt energie uit kennisdeling, je inspireert en enthousiasmeert. Je hebt een grote passie voor
alles wat data driven is en draagt het vakgebied uit binnen de organisatie. Je ondersteunt een team
van data specialisten (Data Engineers, Data Analysten etc.), maar voelt je ook comfortabel bij het
ontwikkelen van software en het werken met CI/CD-pipelines.

Verder is vereist:
- een combinatie van kennis van Data Engineering en de beheersing van didactische vaardigheden;
- kennis van de laatste ontwikkelingen op het vakgebied;
- je neemt een voortrekkersrol richting onze klanten;
- je hebt niet alleen de verwachtingen van de klant helder, maar je hebt ook de risico's in beeld;
- minimaal 3-5 jaar aantoonbare werkervaring als developer of lead developer;
- solide ervaring in data analyse, data pipelines en rapportageomgevingen;
- je bent in staat om mensen te binden en op coachende wijze te sturen en je weet zelfsturing te
  bevorderen.

Je hebt daarnaast ervaring met moderne data architecturen en datawarehouse-concepten, OLAP-tools,
ELT/ETL-tools, metrieken, architectuurprincipes, ontwerpmethodieken en technieken voor het ontwerp
van moderne data platformen, data warehouse, BI-toepassingen en databasetechnologie.

Wat biedt Info Support jou?
- Vakantiegeld, winstuitkering, onkostenvergoeding, bijdrage pensioen
- Leasebudget met tankpas (ook voor het buitenland)
- Laptop en smartphone (of BYOD), facilitering thuiswerkplek
- Een salaris tot EUR 5.025 bruto per maand, afhankelijk van de ervaring die je meeneemt
- Direct een contract voor onbepaalde tijd (op de Managed Services variant), eigen kenniscentrum,
  communities, opleidingsbudget en conferenties
"""

FIT = """# fit - info-support-senior-data-engineer

Fit: 4.2/5

Why: The posting is the senior version of what he does now: understand business data requirements,
design accurate, flexible and extensible data models, then build and run the platform hands-on. At
Van den Bosch Transporten he co-leads the Connectivity track of an Azure Fabric migration
(Seeburger BIS EDI plus Microsoft Graph plus Azure APIM and Functions) and audited 704 ETL processes
for code impact before the migration with 0 reporting breaks; the warehouse under it is SQL Server
with Data Vault 2.0 hubs, links and satellites, temporal tables, window functions and geospatial
logic. At Kuehne+Nagel he built PySpark, SQL and Snowflake ETL in GitLab CI/CD (25% faster
processing) and streamed with Kafka and Spark Structured Streaming (30% lower latency). Reporting is
Power BI with advanced DAX.

Stack match against the advert's named techniques: Azure Data Factory, Data Lake, Python, Streaming,
Airflow, CI/CD and Databricks. Data Factory, Data Lake and Python are daily; streaming is Kafka plus
Spark Structured Streaming in production; CI/CD is GitLab CI/CD. Airflow is not yet in production
(orchestration so far Azure Data Factory plus Power Automate), and Databricks is project and
coursework exposure rather than a production platform. Nothing in the pack claims otherwise.

Gaps / blockers:
- Salary: EUR 4.250 to 5.025 gross per month. Clears his EUR 3.300 floor; quote EUR 4.400 to 5.000
  gross base in any salary field, which sits inside the posted band.
- Dutch: the posting is written in Dutch and includes didactic and client-facing duties, but it
  states no Dutch-fluency requirement. Confirm the working language of the Data & AI unit in the
  first call and note that his Dutch is beginner level so the interview language matters.
- Experience: the advert asks 3-5 years as developer or lead developer. His paid engineering years
  span 2019 to date (NHPC 2 years 2 months, Veena Boutique BI, Kuehne+Nagel internship, Van den
  Bosch contract) plus the MSc and thesis, so he applies on the technical matches.
- Certifications: the advert values ongoing certification (Databricks named as a target platform).
  He holds Power BI advanced DAX and Google Data Analytics certificates; Databricks certification is
  not held yet, and nothing in the pack claims it.
- Visa: Info Support B.V. is on the IND recognised-sponsor register (register line 5515); HSM permit
  to 3 Dec 2026, transfer needed. His MSc (awarded 28 Nov 2025) also keeps him inside the
  reduced-salary criterion.
- ATS: carriere.infosupport.com vacancy page with an on-page SOLLICITEER DIRECT form.

Route: Info Support own careers site (carriere.infosupport.com/vacatures/senior-data-engineer),
on-page application form; email fallback prepared.
"""

TAILOR = {
    "headline": "Vishal Sehgal",
    "summary": (
        "Senior data engineer with a WO Master in Data Science (TU Eindhoven with Tilburg University, "
        "JADS, awarded 28 November 2025). I turn business data requirements into data models and "
        "platforms that run in production: at Van den Bosch Transporten I co-lead the Connectivity "
        "track of an Azure Fabric migration and audited 704 ETL processes for code impact with zero "
        "reporting breaks, on a SQL Server Data Vault 2.0 warehouse. At Kuehne+Nagel I built PySpark, "
        "SQL and Snowflake ETL plus Kafka and Spark Structured Streaming pipelines in GitLab CI/CD. "
        "Azure Data Factory, Data Lake, Python, streaming and CI/CD are my daily tools; Power BI with "
        "advanced DAX is my reporting layer, and I mentor colleagues on data engineering."
    ),
    "skills": [
        {"name": "Data Engineering & Data Platforms",
         "entries": "Data pipelines, ELT/ETL, Data Vault 2.0 (hub, link, satellite), dimensional and semantic data modelling, data quality and auditability, SQL Server, Snowflake, BigQuery, Databricks (project and coursework exposure)"},
        {"name": "Cloud (Azure focus)",
         "entries": "Azure Data Factory, Azure Fabric, Data Lake, Azure APIM, Azure Functions, Key Vault, GCP (Cloud Run, Pub/Sub, BigQuery, Build), AWS S3, Docker"},
        {"name": "Languages & Processing",
         "entries": "Python, SQL, R, PySpark, Spark Structured Streaming, Apache Kafka, dbt"},
        {"name": "Orchestration, CI/CD & Operations",
         "entries": "GitLab CI/CD, Git, scheduled and event-driven pipelines (Azure Data Factory plus Power Automate orchestration so far; Airflow not yet in production), monitoring and alerting"},
        {"name": "Reporting & Analytics",
         "entries": "Power BI with advanced DAX, OLAP concepts, Excel with advanced macros, Dash and Plotly"},
        {"name": "Architecture & Integration",
         "entries": "modern data architecture, API and microservice integration (REST, Flask, Azure APIM, Seeburger BIS EDI), streaming versus batch design, RDF/SPARQL and knowledge graphs"},
        {"name": "AI & LLM Engineering",
         "entries": "RAG (hybrid retrieval, cross-encoder reranking), prompt engineering, agents, LangChain, Copilot Studio, Neo4j knowledge graphs"},
        {"name": "Ways of working",
         "entries": "stakeholder requirement translation, mentoring and knowledge sharing, Scrum and JIRA, technical documentation"},
    ],
    "projects": [
        {"name": "Azure Fabric migration - Connectivity track (Van den Bosch)",
         "desc": "Co-lead of the Seeburger BIS EDI plus Microsoft Graph plus Azure APIM and Functions track; audited 704 ETL processes for code impact with zero reporting breaks."},
        {"name": "SQL Server Data Vault 2.0 warehouse (Van den Bosch)",
         "desc": "Hubs, links and satellites, temporal tables, window functions and geospatial logic powering operational reporting."},
        {"name": "Streaming and batch ETL at Kuehne+Nagel",
         "desc": "PySpark, SQL and Snowflake ETL (25% faster processing) plus Kafka and Spark Structured Streaming (30% lower latency), validated in GitLab CI/CD on AWS S3."},
        {"name": "Business intelligence for a 10-person retailer (Veena Boutique)",
         "desc": "Centralised SQL Server database and reporting suite for daily sales, stock turnover and margin visibility, removing 20+ hours a week of manual entry."},
        {"name": "Semantic Cataloging of AI Models (MSc thesis)",
         "desc": "Neo4j and RDF/SPARQL knowledge base over Hugging Face model cards with a LangChain RAG pipeline and four provenance methods benchmarked."},
    ],
}

LETTER = """Vishal Sehgal
Uilenburg 5G, 5211 EV 's-Hertogenbosch, Netherlands
vishalsehgal414@gmail.com | +31 6 10159758
linkedin.com/in/iamvishalsehgal | github.com/iamvishalsehgal

Dear Info Support Data & AI team,

I am applying for the Senior Data Engineer role in Veenendaal. Turning business data requirements
into data models and platforms that actually run is what my current work is: at Van den Bosch
Transporten I audited 704 ETL processes for code impact before an Azure Fabric migration and moved
them with zero reporting breaks, over a SQL Server Data Vault 2.0 warehouse with temporal tables and
geospatial logic, exposing internal APIs through Azure APIM and Functions.

Your advert names Azure Data Factory, Data Lake, Python, streaming, air flow and CI/CD. Data Factory,
Data Lake and Python are my daily tools; at Kuehne+Nagel I built PySpark, SQL and Snowflake ETL in
GitLab CI/CD that cut processing time by 25%, and streamed data with Kafka and Spark Structured
Streaming to cut latency by 30%. On orchestration my production experience is Azure Data Factory
with event and schedule driven pipelines plus Power Automate where processes need a human in the
loop; Airflow itself I have not yet run in production, and I would pick it up quickly on your
platform side.

I also enjoy the coaching half of this role. I co-lead a migration track and I run knowledge
sessions on the AI service-desk assistant I built over a 19,084-ticket and 106,000-document
knowledge base, so translating between stakeholders and engineers, and between engineers, is
familiar ground.

I am based in 's-Hertogenbosch, a straightforward commute to Veenendaal and hybrid work suits me. I
hold a Highly Skilled Migrant permit valid to 3 December 2026 and a WO Master from TU Eindhoven with
Tilburg University (JADS, awarded 28 November 2025); Info Support B.V. is on the IND
recognised-sponsor register, so a transfer is possible. My current role is a fixed seven-month
contract, 4 May to 3 December 2026, ending by its own terms, and I can start on short notice.

Kind regards,
Vishal Sehgal
"""

MAIL = """Subject: Application for Senior Data Engineer (Data & AI, Veenendaal) - Vishal Sehgal

Recipient: [HR-EMAIL] none-found on the posting page (carriere.infosupport.com carries a question
form and a phone number, no named recruiter address); the on-page SOLLICITEER DIRECT form is the
primary route.

Dear Info Support Hiring Team,

I would like to apply for the Senior Data Engineer role in Veenendaal, in the Data & AI domain.

I am a data engineer with a WO Master in Data Science from TU Eindhoven with Tilburg University
(JADS, awarded 28 November 2025). At Van den Bosch Transporten I audited 704 ETL processes for code
impact before an Azure Fabric migration and moved them with zero reporting breaks, on a SQL Server
Data Vault 2.0 warehouse. At Kuehne+Nagel I built PySpark, SQL and Snowflake ETL in GitLab CI/CD,
cutting processing time by 25%, and streamed with Kafka and Spark Structured Streaming, cutting
latency by 30%. Azure Data Factory, Data Lake and Python are my daily tools and Power BI with
advanced DAX is my reporting layer.

The advert asks for someone who translates business requirements into extensible data models and
mentors colleagues on data engineering. I co-lead a migration track of four engineers and run
knowledge sessions on the service-desk assistant I built over a 19,084-ticket and 106,000-document
knowledge base. Airflow I have not yet run in production; my orchestration so far is Azure Data
Factory with event and schedule driven pipelines.

I hold a Highly Skilled Migrant permit valid to 3 December 2026; Info Support B.V. is on the IND
recognised-sponsor register, so a transfer is possible. My current role is a fixed seven-month
contract, 4 May to 3 December 2026, ending by its own terms, and I can start on short notice.
Expected gross base: EUR 4,400 to 5,000 per month.

Attachments: cv.pdf, cover-letter.pdf.

Kind regards,
Vishal Sehgal
Uilenburg 5G, 5211 EV 's-Hertogenbosch, Netherlands
vishalsehgal414@gmail.com | +31 6 10159758
linkedin.com/in/iamvishalsehgal
"""

FILES = {
    "jd.md": JD, "fit.md": FIT, "cover-letter.md": LETTER, "email-to-hr.md": MAIL,
    "apply-url.txt": "https://carriere.infosupport.com/vacatures/senior-data-engineer\n",
}
for name, content in FILES.items():
    (D / name).write_text(content if content.endswith("\n") else content + "\n")
(D / "tailoring.json").write_text(json.dumps(TAILOR, indent=2, ensure_ascii=False) + "\n")
print("wrote", sorted(list(FILES) + ["tailoring.json"]), "to", D)
