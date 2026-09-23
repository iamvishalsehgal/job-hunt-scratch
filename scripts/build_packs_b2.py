import json, os

WS = "/home/ubuntu/.hermes/profiles/vishal/workspace"
APPS = os.path.join(WS, "applications")

def w(slug, name, content):
    d = os.path.join(APPS, slug)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, name)
    open(p, "w").write(content)
    print("wrote", p, len(content))

# ---------- JPMC jd.md from the live posting text saved by the browser ----------
jpmc_body = open(os.path.expanduser("~/job-hunt-scratch/jd_raw/jpmc.txt")).read()
w("jpmorganchase-software-engineer-iii-databricks", "jd.md",
  "# Software Engineer III (Databricks) - JPMorganChase\n\n"
  "- Company: JPMorganChase\n- Role: Software Engineer III (Databricks)\n- Location: Dublin, Ireland (200 Capital Dock, 79 Sir John Rogerson's Quay)\n"
  "- Requisition: 210768004, Job Category Software Engineering, Business Unit Corporate Sector\n"
  "- Apply URL: https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/job/210768004\n"
  "- Verified live on the employer's own Oracle Recruiting Cloud board: posting date 2026-08-10, no posting end date, Dublin IE\n"
  "- Captured: 2026-09-23 (posting text verbatim from the employer's own job page)\n\n## Posting text\n\n" + jpmc_body + "\n")
w("jpmorganchase-software-engineer-iii-databricks", "apply-url.txt",
  "https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/job/210768004\n")

# ---------- shared close ----------
CLOSE_IE = ("Kind regards,\nVishal Sehgal\nvishalsehgal414@gmail.com | +31 6 10159758 | "
            "linkedin.com/in/iamvishalsehgal | github.com/iamvishalsehgal\n")

# ================= 1. JPMorganChase =================
slug = "jpmorganchase-software-engineer-iii-databricks"
w(slug, "cover-letter.md",
"Dear JPMorgan Chase hiring team,\n\n"
"I am applying for the Software Engineer III (Databricks) role in Dublin, requisition 210768004. Your posting describes data integration across diverse systems, extensible data acquisition and distribution pipelines, and Spark engineering with PySpark at scale. That is the shape of my last three years.\n\n"
"At Kuehne+Nagel I built real-time streaming with Kafka and Spark Structured Streaming into Snowflake: 30% lower data latency and 25% faster processing on large retail datasets, with data validation running in GitLab CI/CD. At Van den Bosch Transporten I co-lead the connectivity track of an Azure Fabric migration and audited 704 ETL processes for code impact before the move, which went through with zero reporting breaks. I model a SQL Server warehouse in Data Vault 2.0 with temporal tables and window functions, and I exposed the order API through Azure APIM using Key Vault managed secrets. Document intake and data security are familiar ground: my retrieval pipeline over a 106,000 document archive begins with PII scrubbing and OCR, and I build on parquet-style columnar storage and Delta table formats.\n\n"
"On two of your named areas I should be straight: Python and PySpark are production strengths, while Java and Terraform are not yet in my production portfolio (my integration work has been Python, REST and Azure APIM). I use AI-assisted developer tooling daily, including a Copilot-based assistant I built that answers about 220 questions a week over a 19,084 ticket knowledge base, and I would expect to pick the rest up quickly inside your engineering patterns.\n\n"
"My current role is a fixed seven-month contract, 4 May to 3 December 2026, ending by its own terms, and my Dutch residence permit runs to the same date. For this Dublin role I would need employer support for an Irish employment permit, and I am ready to relocate.\n\n" + CLOSE_IE)

json.dump({
 "company": "JPMorganChase", "role": "Software Engineer III (Databricks)", "headline": "Vishal Sehgal",
 "summary": "Data engineer with production Spark experience: at Kuehne+Nagel I built Kafka and Spark Structured Streaming pipelines into Snowflake (30% lower latency, 25% faster processing) with validation in GitLab CI/CD, and at Van den Bosch Transporten I co-lead the connectivity track of an Azure Fabric migration and model a SQL Server warehouse in Data Vault 2.0. My integration work covers REST APIs, Azure APIM with Key Vault secrets and ETL audits across 704 processes with zero reporting breaks. Python and PySpark are my production core, with AI-assisted developer tooling in daily use.",
 "skills": [
  {"name": "Spark & Big Data Engineering", "entries": "PySpark, Spark Structured Streaming, Apache Kafka, Databricks (working stack, Databricks and Spark interchangeable for me), batch and streaming pipeline design, large-scale dataset optimisation"},
  {"name": "Cloud Data Platforms", "entries": "Snowflake ETL, AWS S3, Azure (Fabric, Data Factory, Functions, APIM), GCP (BigQuery, Pub/Sub, Cloud Run); columnar and lakehouse formats (Parquet, Delta-style tables) and warehouse, lake and data-modelling concepts"},
  {"name": "SQL, Modelling & Warehousing", "entries": "Advanced SQL (window functions, CTEs, query tuning), SQL Server, Oracle, MySQL, PostgreSQL, Data Vault 2.0 hub/link/satellite modelling, temporal tables, Data Lake and Data Security fundamentals, geospatial logic (Haversine)"},
  {"name": "Programming & APIs", "entries": "Python (primary), SQL, R, ASP, Flask and REST microservices, Azure APIM subscription-key auth with Key Vault managed secrets, JSON and YAML configuration; Java not yet in production"},
  {"name": "CI/CD & Engineering Practice", "entries": "Git and GitLab CI/CD pipelines, automated data validation and pipeline testing, code-impact audits before migration, Docker, Git, JIRA and Scrum delivery"},
  {"name": "Data Integration & Analysis", "entries": "Extract, transform and distribute data across ERP, EDI and API sources (Seeburger BIS EDI, Microsoft Graph), 704-process ETL audit with zero reporting breaks, problem-solving and complex analysis for business intelligence integration"},
  {"name": "AI-Assisted Engineering", "entries": "RAG pipelines with hybrid retrieval and reranking, knowledge graphs (Neo4j, RDF/SPARQL), PII scrubbing and OCR over a 106,000 document archive, Copilot-based assistant handling about 220 questions a week"},
  {"name": "Collaboration", "entries": "Cross-functional work with product, finance and operations teams, remote and distributed collaboration, documentation and hand-over of design decisions; English fluent (IELTS 8.0 overall, CEFR C1)"}
 ],
 "projects": [
  {"name": "Real-time streaming into Snowflake (Kuehne+Nagel)", "desc": "Kafka plus Spark Structured Streaming with PySpark and SQL ETL, 30% lower data latency and 25% faster processing, validation and pipeline tests in GitLab CI/CD"},
  {"name": "Azure Fabric migration connectivity track (Van den Bosch Transporten)", "desc": "Co-lead of Seeburger BIS EDI, Microsoft Graph and Azure APIM/Functions integration, 704 ETL processes audited for code impact before the move with zero reporting breaks"},
  {"name": "SQL Server warehouse in Data Vault 2.0 (Van den Bosch Transporten)", "desc": "Hub, link and satellite models with temporal tables and window functions, feeding Power BI and DAX reporting across the organisation"},
  {"name": "Scalable NBA data architecture (GCP)", "desc": "Spark cluster with Kafka streaming and PySpark batch ETL into BigQuery, orchestrated cloud build and deployment"},
  {"name": "RAG and knowledge graph over the ticket archive (Van den Bosch Transporten)", "desc": "PII scrubbing, OCR and chunking over 19,084 tickets and 106,000 documents, answering about 220 questions a week"}
 ]}, open(os.path.join(APPS, slug, "tailoring.json"), "w"), indent=1, ensure_ascii=False)

w(slug, "fit.md",
"# Fit: JPMorganChase - Software Engineer III (Databricks), Dublin IE\n\n"
"Score: 4/5\n\n"
"- Spark/PySpark with Databricks and Snowflake ETL is the centre of the role and the centre of my last internship plus current work: Kafka and Spark Structured Streaming (30% lower latency), PySpark and SQL ETL (25% faster), Data Vault 2.0 warehouse modelling.\n"
"- Data integration, ETL auditing (704 processes, zero breaks), API exposure through Azure APIM with Key Vault and columnar/Delta-style storage map directly to the acquisition, transformation and distribution responsibilities.\n"
"- Big Data with Databricks plus AWS is the gap area: my AWS experience is S3, and Airflow, Java, Terraform and Jenkins are not yet in production (my CI/CD is GitLab, orchestration is Fabric/ADF).\n\n"
"Blockers: no stated salary band in the posting (ask EUR 4,400-5,000 if asked); Dublin role so Irish employment permit support is needed, stated openly in the letter. No Dutch requirement, JD in English.\n"
"Gate: gates/eu_scope_gate.py check --country IE exit 0 (tier1, sponsorship not stated, manual hand-off not allowed).\n")

w(slug, "email-to-hr.md",
"To: [ADDRESS TO RESOLVE AND PASS gates/email_guard.py BEFORE ANY SEND]\n"
"Subject: Application - Software Engineer III (Databricks), Dublin (210768004) - Vishal Sehgal\n\n"
"Dear JPMorgan Chase hiring team,\n\n"
"I have applied through your careers site for the Software Engineer III (Databricks) role in Dublin (requisition 210768004). My CV and cover letter are attached.\n\n"
"In short: at Kuehne+Nagel I built Kafka and Spark Structured Streaming pipelines into Snowflake (30% lower data latency, 25% faster processing) with validation in GitLab CI/CD, and at Van den Bosch Transporten I co-lead the connectivity track of an Azure Fabric migration, audited 704 ETL processes for code impact before the move, and model a SQL Server warehouse in Data Vault 2.0.\n\n"
"My current role is a fixed seven-month contract, 4 May to 3 December 2026, ending by its own terms, and my Dutch residence permit runs to the same date. For a Dublin role I would need employer support for an Irish employment permit.\n\n"
"Attachments: cv.pdf, cover-letter.pdf\n\n"
"Kind regards,\nVishal Sehgal\nvishalsehgal414@gmail.com | +31 6 10159758 | linkedin.com/in/iamvishalsehgal\n")

# ================= 2. Euronext =================
slug = "euronext-data-engineer-for-ai"
w(slug, "cover-letter.md",
"Dear Euronext hiring team,\n\n"
"I am applying for the Data Engineer for AI role in Dublin, requisition R28530. You are standing up an AI R&D team whose first job is to make data accessible, reliable and governed enough for experimentation, and the responsibilities you list are ones I already carry.\n\n"
"At Van den Bosch Transporten I co-lead the connectivity track of an Azure Fabric migration, audited 704 ETL processes for code impact before the move with zero reporting breaks, and exposed internal APIs through Azure APIM with Key Vault managed secrets. On the AI side, my MSc thesis, Semantic Cataloging of AI Models using LLMs and Knowledge Graphs, built a Neo4j and RDF/SPARQL knowledge base from real source data with a Gemini and LangChain retrieval pipeline, and benchmarked four provenance methods for answer accuracy. At work I built a retrieval and knowledge-graph pipeline that starts with PII scrubbing and OCR across 106,000 documents and 19,084 tickets. Both are the discipline your role names: cleansed and enriched datasets, governed access, reusable data products, and monitoring that keeps experiments honest.\n\n"
"Advanced SQL and Python are my daily tools (PySpark, dbt, Snowflake), with cloud data work on Microsoft Fabric, Data Factory and Functions alongside GCP, and ML lifecycle practice from an end-to-end Vertex AI MLOps project with champion-challenger model selection. Synapse specifically is not yet in my portfolio; my Azure data work is Fabric and Data Factory based, which makes the transition close.\n\n"
"My current role is a fixed seven-month contract, 4 May to 3 December 2026, ending by its own terms, and my Dutch residence permit runs to the same date. For this Dublin role I would need employer support for an Irish employment permit, and I am ready to relocate.\n\n" + CLOSE_IE)

json.dump({
 "company": "Euronext", "role": "Data Engineer for AI", "headline": "Vishal Sehgal",
 "summary": "Data engineer focused on the foundations AI work depends on: pipelines, cleansed and enriched datasets and governed access. At Van den Bosch Transporten I co-lead the connectivity track of an Azure Fabric migration and built retrieval and knowledge-graph pipelines that begin with PII scrubbing and OCR over 106,000 documents. My MSc thesis, Semantic Cataloging of AI Models using LLMs and Knowledge Graphs, was a Neo4j and RDF/SPARQL knowledge base built from real source data with benchmarked provenance. Advanced SQL and Python are daily tools, with an MLOps project on Vertex AI behind them.",
 "skills": [
  {"name": "Cloud Data Services", "entries": "Microsoft Fabric (co-lead of a Fabric migration connectivity track), Azure Data Factory, Azure Functions, Azure APIM, Databricks and Spark (PySpark, Spark Structured Streaming), Snowflake, GCP (BigQuery, Pub/Sub, Cloud Run); Synapse not yet used in production"},
  {"name": "Data Pipelines & Platform Engineering", "entries": "Modern pipeline design (batch and streaming), Kafka, dbt, ETL orchestration, code-impact auditing across 704 ETL processes with zero reporting breaks, reusable data products and reusable connectivity patterns"},
  {"name": "SQL & Python", "entries": "Advanced SQL (window functions, CTEs, temporal tables, query tuning), Python for pipelines, testing and APIs (Flask, REST), PySpark at scale, data validation and reconciliation checks"},
  {"name": "AI and ML Lifecycle", "entries": "Training dataset preparation, feature engineering, cleansing and enrichment, RAG pipelines with hybrid retrieval and reranking, knowledge graphs (Neo4j, RDF/SPARQL), model evaluation with provenance benchmarking, BERT and BERTopic text analytics"},
  {"name": "Data Governance, Security & Monitoring", "entries": "PII scrubbing and OCR before ingestion, Key Vault managed secrets, subscription-key API auth, access control on exposed services, pipeline monitoring and failure triage, data quality checks"},
  {"name": "MLOps & Operationalisation", "entries": "End-to-end MLOps on Vertex AI with champion-challenger model selection, Flask API and Cloud Run deployment, Docker and GitLab CI/CD for reproducible builds"},
  {"name": "Data Modelling", "entries": "Data Vault 2.0 hub/link/satellite modelling, dimensional design, temporal and geospatial modelling (Haversine), warehouse and lakehouse patterns on SQL Server, Snowflake and BigQuery"},
  {"name": "Collaboration & Communication", "entries": "Partnering with business stakeholders and data owners, standards work across distributed teams (Erp NL with Porto-facing patterns), documentation of design decisions, English fluent (IELTS 8.0 overall, CEFR C1)"}
 ],
 "projects": [
  {"name": "Semantic Cataloging of AI Models using LLMs and Knowledge Graphs (MSc thesis)", "desc": "Neo4j and RDF/SPARQL knowledge base built from Hugging Face model cards with entity and relationship modelling, Gemini plus LangChain retrieval, four provenance methods benchmarked for answer accuracy"},
  {"name": "Azure Fabric migration connectivity track (Van den Bosch Transporten)", "desc": "Co-lead of Seeburger BIS EDI, Microsoft Graph and APIM/Functions integration, 704 ETL processes audited for code impact before the move with zero reporting breaks"},
  {"name": "RAG and knowledge-graph pipeline over the ticket archive (Van den Bosch Transporten)", "desc": "PII scrubbing, OCR and chunking across 19,084 tickets and 106,000 documents, feeding an internal assistant answering about 220 questions a week"},
  {"name": "End-to-end MLOps, stroke prediction", "desc": "Vertex AI pipelines (KFP) with champion-challenger selection, Flask API and UI on Cloud Run, reproducible deployment through Cloud Build and Docker"},
  {"name": "Scalable NBA data architecture (GCP)", "desc": "Spark cluster with Kafka streaming and PySpark batch ETL into BigQuery for training-scale data preparation"}
 ]}, open(os.path.join(APPS, slug, "tailoring.json"), "w"), indent=1, ensure_ascii=False)

w(slug, "fit.md",
"# Fit: Euronext - Data Engineer for AI, Dublin IE\n\n"
"Score: 3.5/5\n\n"
"- Azure Data Services and Microsoft Fabric are exactly my current platform: I co-lead the connectivity track of a Fabric migration, with Data Factory and Functions, and audit 704 ETL processes.\n"
"- The AI data foundation responsibilities (cleansed and enriched datasets, training data prep, feature engineering, governance and monitoring) match my MSc thesis on knowledge graphs plus RAG and my production PII-scrubbing and OCR pipeline.\n"
"- Gaps: no Snowflake-to-Fabric migration at group scale, Synapse not held, MLOps exposure is project-based (Vertex AI) rather than platform ownership.\n\n"
"Blockers: Dublin role, needs Irish employment permit support (stated openly); no posted salary band (ask EUR 4,400-5,000). English-language JD, no Dutch requirement.\n"
"Gate: gates/eu_scope_gate.py check --country IE exit 0 (tier1, sponsorship not stated, manual hand-off not allowed).\n")

w(slug, "email-to-hr.md",
"To: [ADDRESS TO RESOLVE AND PASS gates/email_guard.py BEFORE ANY SEND]\n"
"Subject: Application - Data Engineer for AI, Dublin (R28530) - Vishal Sehgal\n\n"
"Dear Euronext hiring team,\n\n"
"I have applied through your careers site for the Data Engineer for AI role in Dublin (R28530). My CV and cover letter are attached.\n\n"
"In short: at Van den Bosch Transporten I co-lead the connectivity track of an Azure Fabric migration, exposed internal APIs through Azure APIM with Key Vault managed secrets, and built retrieval and knowledge-graph pipelines that start with PII scrubbing and OCR over 106,000 documents. My MSc thesis built a Neo4j and RDF/SPARQL knowledge base from real source data with a Gemini and LangChain retrieval pipeline and four benchmarked provenance methods.\n\n"
"My current role is a fixed seven-month contract, 4 May to 3 December 2026, ending by its own terms, and my Dutch residence permit runs to the same date. For a Dublin role I would need employer support for an Irish employment permit.\n\n"
"Attachments: cv.pdf, cover-letter.pdf\n\n"
"Kind regards,\nVishal Sehgal\nvishalsehgal414@gmail.com | +31 6 10159758 | linkedin.com/in/iamvishalsehgal\n")

# ================= 3. Salesforce =================
slug = "salesforce-data-engineering-senior-associate"
w(slug, "cover-letter.md",
"Dear Salesforce hiring team,\n\n"
"I am applying for the Data Engineering Senior Associate role in Dublin, requisition JR359930. Your posting is a build-and-run role: ETL and ELT with Python, Snowflake and SQL, orchestrated workflows, integrations between Salesforce and enterprise systems, production monitoring and root cause analysis. That mix is what I do now.\n\n"
"At Kuehne+Nagel I built Snowflake ETL with PySpark and SQL, 25% faster processing on large retail datasets, and real-time streaming with Kafka and Spark Structured Streaming, 30% lower data latency, with data validation and pipeline tests running in GitLab CI/CD. At Van den Bosch Transporten I co-lead the connectivity track of an Azure Fabric migration and audited 704 ETL processes for code impact before the move with zero reporting breaks. On the run side, I built the retrieval layer behind an internal assistant that answers about 220 questions a week over 19,084 tickets and 106,000 documents, which is the knowledge-retrieval approach your posting describes for production support, and I troubleshoot across Seeburger BIS EDI, APIM and Azure Functions when routing breaks. Earlier, at Veena Boutique, I owned month-end reconciliation and cash-flow reporting at 100% accuracy for a ten-person team, so close-cycle pressure is familiar.\n\n"
"On tooling I will be straight: Python, SQL, Snowflake and GitLab CI/CD are my production strengths, while Airflow, MuleSoft and Informatica are not yet in my portfolio; my integrations have been REST and Azure APIM, and my orchestration Fabric, Data Factory and CI/CD based. I am comfortable in an on-call rotation and I document corrective actions to closure.\n\n"
"My current role is a fixed seven-month contract, 4 May to 3 December 2026, ending by its own terms, and my Dutch residence permit runs to the same date. For this Dublin role I would need employer support for an Irish employment permit, and I am ready to relocate.\n\n" + CLOSE_IE)

json.dump({
 "company": "Salesforce", "role": "Data Engineering Senior Associate", "headline": "Vishal Sehgal",
 "summary": "Data engineer with both build and production support experience: Snowflake ETL with PySpark and SQL (25% faster processing), Kafka and Spark Structured Streaming (30% lower latency) with validation in GitLab CI/CD, and a 704-process ETL audit before an Azure Fabric migration that went through with zero reporting breaks. Current integration work spans Seeburger BIS EDI, REST APIs and Azure APIM with Key Vault secrets, plus the retrieval layer of an internal assistant answering about 220 questions a week over 19,084 tickets. Month-end reconciliation and incident triage are part of my working history.",
 "skills": [
  {"name": "ETL/ELT Engineering", "entries": "Python and PySpark ETL, SQL transformations, Snowflake ETL (25% faster processing on large retail datasets), batch and streaming ingestion with Kafka and Spark Structured Streaming, data validation and pipeline tests in GitLab CI/CD; Informatica and BusinessObjects Data Integrator not yet in my portfolio"},
  {"name": "Orchestration & Scheduling", "entries": "Workflow orchestration through Azure Data Factory and Fabric pipelines, scheduled jobs with retry and failure handling in GitLab CI/CD, dependency and data-availability monitoring, release and deployment planning; Apache Airflow not yet in production use"},
  {"name": "APIs & Integrations", "entries": "REST API design and consumption, Flask microservices, Azure APIM exposure with Key Vault managed secrets and subscription-key auth, EDI integration through Seeburger BIS, Microsoft Graph data flows; MuleSoft not yet held, my integration stack is REST, APIM and EDI"},
  {"name": "Production Support & Incident Work", "entries": "Incident triage and restoration across EDI, API and function routing chains, root cause analysis with corrective actions tracked to closure, monitoring of jobs, interfaces, data availability and quality, knowledge retrieval for support (assistant over 19,084 tickets answering about 220 questions a week)"},
  {"name": "SQL & Data Platforms", "entries": "Advanced SQL (window functions, CTEs, temporal tables), SQL Server, Oracle, MySQL, PostgreSQL, Snowflake, BigQuery, Data Vault 2.0 hub/link/satellite modelling and dimensional design, Power BI with advanced DAX for reporting and controls"},
  {"name": "Finance-adjacent Reporting", "entries": "Month-end reconciliation and cash-flow models at 100% accuracy for a ten-person business, procurement and margin analysis from sales trend data, cost and control reporting for non-technical owners; SoX and audit co-operation would be new process exposure on top of that"},
  {"name": "Programming & Cloud", "entries": "Python (primary), SQL, R, Azure (Fabric, Data Factory, Functions, APIM), GCP (BigQuery, Pub/Sub, Cloud Run), AWS S3, Docker, Git and GitLab CI/CD"},
  {"name": "Collaboration", "entries": "Cross-functional work with finance, operations and product stakeholders, remote and geographically distributed teams, agile delivery with Scrum and JIRA, documentation of corrective and preventive actions, English fluent (IELTS 8.0 overall, CEFR C1)"}
 ],
 "projects": [
  {"name": "Snowflake ETL and streaming pipelines (Kuehne+Nagel)", "desc": "PySpark and SQL ETL with Kafka and Spark Structured Streaming, 25% faster processing and 30% lower latency, validation and pipeline tests in GitLab CI/CD"},
  {"name": "Azure Fabric migration connectivity track (Van den Bosch Transporten)", "desc": "Co-lead of EDI, Microsoft Graph and APIM/Functions integration, 704 ETL processes audited for code impact before the move with zero reporting breaks"},
  {"name": "Knowledge retrieval for production support (Van den Bosch Transporten)", "desc": "RAG and knowledge-graph pipeline over 19,084 tickets and 106,000 documents, PII scrubbing and OCR first, answering about 220 questions a week"},
  {"name": "SQL Server warehouse and reporting layer in Data Vault 2.0 (Van den Bosch Transporten)", "desc": "Hub, link and satellite models with temporal tables and window functions feeding Power BI and DAX reporting"},
  {"name": "Month-end reconciliation and BI suite (Veena Boutique)", "desc": "SQL Server consolidation of sales and inventory records, dashboards for daily sales and margins, month-end cash-flow models at 100% accuracy"}
 ]}, open(os.path.join(APPS, slug, "tailoring.json"), "w"), indent=1, ensure_ascii=False)

w(slug, "fit.md",
"# Fit: Salesforce - Data Engineering Senior Associate, Dublin IE\n\n"
"Score: 3.5/5\n\n"
"- ETL/ELT with Python, SQL and Snowflake plus production support is directly my current and previous work: Kafka and Spark streaming (30% lower latency), Snowflake ETL (25% faster), 704 ETL processes audited pre-migration with zero breaks.\n"
"- The incident and root cause responsibilities map to real break-fix work on Seeburger EDI, APIM and Azure Functions routing, and to the ticket-based retrieval assistant I built (19,084 tickets, 220 questions a week).\n"
"- Gaps: Airflow, MuleSoft and Informatica are not in my portfolio, and the 3-7 years band is met in the lower half (about 4 years of data engineering plus 2 years of software development).\n\n"
"Blockers: Dublin role, Irish employment permit support needed (stated openly in the letter); no posted salary band (ask EUR 4,400-5,000). English-language JD.\n"
"Gate: gates/eu_scope_gate.py check --country IE exit 0 (tier1, sponsorship not stated, manual hand-off not allowed).\n")

w(slug, "email-to-hr.md",
"To: [ADDRESS TO RESOLVE AND PASS gates/email_guard.py BEFORE ANY SEND]\n"
"Subject: Application - Data Engineering Senior Associate, Dublin (JR359930) - Vishal Sehgal\n\n"
"Dear Salesforce hiring team,\n\n"
"I have applied through your careers site for the Data Engineering Senior Associate role in Dublin (JR359930). My CV and cover letter are attached.\n\n"
"In short: at Kuehne+Nagel I built Snowflake ETL with PySpark and SQL (25% faster processing) and Kafka with Spark Structured Streaming (30% lower latency), with validation in GitLab CI/CD. At Van den Bosch Transporten I co-lead the connectivity track of an Azure Fabric migration, audited 704 ETL processes for code impact before the move, and built the knowledge-retrieval layer behind an internal assistant that answers about 220 questions a week over 19,084 tickets.\n\n"
"My current role is a fixed seven-month contract, 4 May to 3 December 2026, ending by its own terms, and my Dutch residence permit runs to the same date. For a Dublin role I would need employer support for an Irish employment permit.\n\n"
"Attachments: cv.pdf, cover-letter.pdf\n\n"
"Kind regards,\nVishal Sehgal\nvishalsehgal414@gmail.com | +31 6 10159758 | linkedin.com/in/iamvishalsehgal\n")

# ================= 4. Basic-Fit =================
slug = "basic-fit-club-data-analyst"
w(slug, "cover-letter.md",
"Dear Basic-Fit hiring team,\n\n"
"I am applying for the Club Data Analyst role in Hoofddorp, requisition R55713. Turning facility ticket and maintenance data into standing dashboards, flagged anomalies and cost figures is very close to the work I do now.\n\n"
"At Van den Bosch Transporten I built the retrieval and reporting layer behind an internal service-desk assistant over an archive of 19,084 tickets and 106,000 documents: PII scrubbing, OCR and chunking first, then signal that a manager can act on. On the data side I model a SQL Server warehouse in Data Vault 2.0 with temporal tables, window functions and geospatial logic, and I audited 704 ETL processes for code impact before a platform migration, so tracing a recurring defect across a messy process chain is familiar ground. PySpark and Spark are my daily tools (Databricks is my working platform for that work), and dashboards are how I have delivered before: at Veena Boutique my dashboards were the owner's first real view of sales, stock turnover and margin, and the seasonal trend analysis behind them cut overstock directly, with month-end reconciliation at 100% accuracy.\n\n"
"On the facility domain I want to be straight: my ticketing and asset-adjacent analysis has been on service-desk data rather than building maintenance, so supplier SLA benchmarking and cost-per-intervention would be new ground I would learn from your facility managers, whose questions are the kind I like having to answer.\n\n"
"My current role is a fixed seven-month contract, 4 May to 3 December 2026, ending by its own terms, and my Dutch residence permit runs to the same date; a new employer must be an IND-recognised sponsor.\n\n" + CLOSE_IE)

json.dump({
 "company": "Basic-Fit", "role": "Club Data Analyst", "headline": "Vishal Sehgal",
 "summary": "Data analyst and engineer who turns operational records into dashboards and cost signal: at Van den Bosch Transporten I built the reporting and retrieval layer over a 19,084 ticket and 106,000 document archive, and I model a SQL Server warehouse in Data Vault 2.0 with temporal tables and window functions. My earlier BI suite for Veena Boutique gave the owner first visibility of sales, stock turnover and margin, with procurement savings from seasonal trend analysis. PySpark and Spark on Databricks are my daily tools, with advanced SQL and Power BI/DAX beside them.",
 "skills": [
  {"name": "SQL & Databricks", "entries": "Advanced SQL (window functions, CTEs, temporal tables, query tuning, own views and aggregations on existing data), PySpark and Spark on Databricks as my working platform, Snowflake, SQL Server, BigQuery, dbt"},
  {"name": "Dashboards & Reporting", "entries": "Power BI with advanced DAX, self-serve dashboards that stay standing rather than one-off analyses, Plotly and Dash, Excel with advanced models, month-end and cash-flow reporting at 100% accuracy"},
  {"name": "Analysis & Statistics", "entries": "Statistical and trend analysis, anomaly and root cause investigation across process chains (704 ETL processes audited for code impact with zero reporting breaks), RFM and K-means segmentation, survival analysis, seasonal trend analysis for procurement decisions"},
  {"name": "Ticket & Operational Data", "entries": "Service-desk ticket data intake and analysis at scale (19,084 tickets), PII scrubbing, OCR and chunking over 106,000 documents, knowledge retrieval that answers about 220 questions a week, ETL and data-quality checks across ERP and maintenance-adjacent sources; building-maintenance and facility domain data would be new ground"},
  {"name": "Cost and Supplier Analysis", "entries": "Cost and margin analysis from sales, inventory and spend records, overstock reduction through seasonal demand analysis, benchmarking and comparison work for non-technical owners; supplier SLA benchmarking specifically would be new"},
  {"name": "Pipelines & Integration", "entries": "ETL development in Python and PySpark, Azure Data Factory and Fabric pipelines, REST and API integration through Azure APIM, GitLab CI/CD, Docker, Git"},
  {"name": "Stakeholder Work", "entries": "Translating data questions from managers into models and dashboards, written documentation of findings, presenting results to non-technical audiences, English fluent (IELTS 8.0 overall, CEFR C1), Dutch beginner and improving"},
  {"name": "Education", "entries": "MSc Data Science in Business and Entrepreneurship, TU Eindhoven with Tilburg University (JADS), awarded 28 November 2025, NLQF 7 / EQF 7; B.Tech Computer Science and Engineering"}
 ],
 "projects": [
  {"name": "Ticket and document analytics pipeline (Van den Bosch Transporten)", "desc": "PII scrubbing, OCR and chunking across 19,084 tickets and 106,000 documents with reporting that answers about 220 questions a week for managers"},
  {"name": "SQL Server warehouse and reporting in Data Vault 2.0 (Van den Bosch Transporten)", "desc": "Hub, link and satellite models with temporal tables and window functions feeding Power BI dashboards; 704 ETL processes audited for code impact before migration with zero reporting breaks"},
  {"name": "BI dashboard suite (Veena Boutique)", "desc": "Daily sales, stock turnover and margin dashboards giving the owner first performance visibility, procurement optimised through seasonal trend analysis, and 20+ hours a week of manual entry removed"},
  {"name": "Comfy Data Analytics", "desc": "2.6 million transactions segmented with RFM and K-means plus survival analysis to explain retention and churn"},
  {"name": "Semantic Cataloging of AI Models using LLMs and Knowledge Graphs (MSc thesis)", "desc": "Neo4j and RDF/SPARQL knowledge base built from real source data with a retrieval pipeline and benchmarked provenance"}
 ]}, open(os.path.join(APPS, slug, "tailoring.json"), "w"), indent=1, ensure_ascii=False)

w(slug, "fit.md",
"# Fit: Basic-Fit - Club Data Analyst, Hoofddorp NL\n\n"
"Score: 3/5\n\n"
"- Strong SQL plus dashboards plus statistical analysis is the core of the role and the core of my profile: Power BI with advanced DAX, Data Vault 2.0 warehouse modelling, RFM and survival analysis, and a BI suite that gave a business its first performance visibility.\n"
"- Ticket and operational record analysis is genuine current work: 19,084 tickets and 106,000 documents with PII scrubbing, OCR and chunking, plus a 704-process audit that shows how I trace a recurring defect across a process chain.\n"
"- The stated requirement of facility and building-management data knowledge (maintenance, ticketing, asset or supplier/SLA data) is the weak point: my ticket data is service-desk, not maintenance, and cost-per-intervention and supplier benchmarking are new.\n\n"
"Salary: posted EUR 3,500-5,500 gross per month (40h) - posted minimum is below the EUR 4,000 target, so the ask stays EUR 4,400-5,000. IND sponsor confirmed for the role per the tracker note (Basic Fit International B.V., Hoofddorp).\n"
"Blockers: none hard (no Dutch-fluency requirement stated, posting is in English). 4 days office, 1 day home, Hoofddorp - commutable and within his relocation openness.\n"
"Board: own Workday tenant basicfit.wd103.myworkdayjobs.com, R55713, live since 2026-09-15 (resolved from the LinkedIn mirror; never Easy Apply).\n")

w(slug, "email-to-hr.md",
"To: [ADDRESS TO RESOLVE AND PASS gates/email_guard.py BEFORE ANY SEND]\n"
"Subject: Application - Club Data Analyst, Hoofddorp (R55713) - Vishal Sehgal\n\n"
"Dear Basic-Fit hiring team,\n\n"
"I have applied through your careers site for the Club Data Analyst role in Hoofddorp (R55713). My CV and cover letter are attached.\n\n"
"In short: at Van den Bosch Transporten I built the reporting and retrieval layer over 19,084 tickets and 106,000 documents, with PII scrubbing, OCR and chunking first, and I model a SQL Server warehouse in Data Vault 2.0 with Power BI dashboards on top. Earlier, my BI suite gave a retail owner first visibility of sales, stock turnover and margin, and cut overstock through seasonal trend analysis.\n\n"
"My current role is a fixed seven-month contract, 4 May to 3 December 2026, ending by its own terms, and my Dutch residence permit runs to the same date; a new employer must be an IND-recognised sponsor.\n\n"
"Attachments: cv.pdf, cover-letter.pdf\n\n"
"Kind regards,\nVishal Sehgal\nvishalsehgal414@gmail.com | +31 6 10159758 | linkedin.com/in/iamvishalsehgal\n")

w("basic-fit-club-data-analyst", "apply-url.txt",
  "https://basicfit.wd103.myworkdayjobs.com/BasicFit_Career_Site_NL/job/Hoofddorp/Club-Data-Analyst_R55713\n")
print("ALL PACK DRAFTS DONE")
