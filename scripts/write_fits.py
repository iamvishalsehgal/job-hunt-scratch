import os, subprocess

WS = "/home/ubuntu/.hermes/profiles/vishal/workspace"
APPS = os.path.join(WS, "applications")

FITS = {}

FITS["haskoning-bi-consultant-asset-management"] = """# fit - haskoning-bi-consultant-asset-management

Fit: 4.1/5 on the technical content, HARD SKIP on language (rule 4(a))

Why: The role is BI consultancy inside the Asset Management advisory group (Data Solutions team, 5 FTE): data models and pipelines, Power BI dashboards, Azure, GitHub, Python, SQL, ETL, AI assisted development, for 1 to 3 years of pipeline and warehousing experience. That is his current work: the connectivity track of an Azure Fabric migration with 704 ETL processes audited for code impact and zero reporting breaks, a SQL Server Data Vault 2.0 warehouse, Powers BI with advanced DAX. Band EUR 3,146 to EUR 5,500 gross per month, so the top clears his EUR 4,000 target.

Blocker (hard skip, rule 4(a) Dutch): the posting is written in Dutch and states "vragen we vaardigheid van de Nederlandse taal op minimaal B2 niveau en de bereidheid om dit te blijven ontwikkelen" (Dutch at B2 minimum). gates/dutch_gate.py returns exit 11 SKIP_DUTCH_LANGUAGE (34 Dutch markers, 3.81 per 1k chars). He is at Dutch A2-B1 and the clients are Dutch asset managers, so the working language is out of reach. No CV, no letter, no form, no email spent.

Also noted: standplaats is chosen with the candidate across Amersfoort, Amsterdam, Eindhoven and Maastricht. Haskoning Nederland B.V. and Koninklijke HaskoningDHV Groep B.V. are on the IND recognised-sponsor register, so sponsorship would not have been the obstacle; the language gate is decisive.

Route: not attempted (hard skip). apply_url: https://nl.linkedin.com/jobs/view/bi-consultant-asset-management-at-haskoning-4460528111
"""

FITS["pggm-medior-azure-devops"] = """# fit - pggm-medior-azure-devops

Fit: 4.0/5 on the discovery score, HARD SKIP on language (rule 4(a))

Why: The advertised stack overlaps only partly with his data engineering profile. The role is a .NET developer building APIs, integrations and low-code flows around Dynamics 365 and the Power Platform (Power Automate, Power Apps, Logic Apps), Azure API Management, Function Apps, Service Bus and Dataverse solutions. His Azure work is real (APIM, Functions, Data Factory, Fabric) and API integration is central to his current job, which is why the discovery fit was high, but the core languages here are C# .NET and JavaScript.

Blocker (hard skip, rule 4(a) Dutch): gates/dutch_gate.py returns exit 10 SKIP_DUTCH_FLUENCY on "Goede beheersing van de Nederlandse en Engelse taal" (good command of Dutch and English). Posting is otherwise Dutch throughout.

Second blocker, would have been disqualifying on its own: "Certificering Azure 204 is een must" (Azure 204 certification is required) plus "3+ jaar ervaring met het ontwikkelen van oplossingen in een Microsoft-omgeving" (.NET development experience he does not hold).

Package: EUR 4,101 to EUR 6,647 gross per month, scale 15/16, based on 36 hours, vacation pay and a thirteenth month. PGGM N.V. is on the IND recognised-sponsor register, so transfer would be possible. No CV, no letter, no form, no email spent.

Route: not attempted (hard skip). apply_url: https://nl.linkedin.com/jobs/view/medior-azure-devops-at-pggm-4468399993
"""

FITS["deloitte-junior-engineer-next-generation-customer-solutions"] = """# fit - deloitte-junior-engineer-next-generation-customer-solutions

Fit: 4.0/5 on the discovery score, HARD SKIP on language (rule 4(a))

Why: Deloitte Digital Customer team, Amsterdam: entry-level developer who grows into Developer, Release Engineer, System Integrator or Architect on Salesforce and MuleSoft, with Apex, JavaScript, SQL, HTML/CSS, Git branching and basic CI/CD. Python and SQL from the advert he has; the Salesforce and Mendix platform work would be new training ground, and the advert states all candidates get Salesforce and Agile training.

Blocker (hard skip, rule 4(a) Dutch): gates/dutch_gate.py returns exit 10 SKIP_DUTCH_FLUENCY on "Een uitstekende beheersing van de Nederlandse en Engelse taal in woord en geschrift is een vereiste" (excellent command of Dutch and English required). That is client-facing consultancy in Dutch.

Also noted: no salary is published (profit share on top of a fixed salary only), so the band cannot be checked against his EUR 3,300 floor; the role is instapniveau. Deloitte Consultative Services B.V., Deloitte Accountancy & Advies B.V. and Deloitte Group Support Center B.V. are on the IND register. No CV, no letter, no form, no email spent.

Route: not attempted (hard skip). apply_url: https://nl.linkedin.com/jobs/view/junior-engineer-next-generation-customer-solutions-at-deloitte-4465995041
"""

FITS["sogeti-medior-ai-engineer"] = """# fit - sogeti-medior-ai-engineer

Fit: 4.2/5 on the technical content, HARD SKIP on language (rule 4(a))

Why: The strongest technical match in this batch. The role asks for Generative AI with LLMs and RAG, Agentic AI with guardrailed task execution, AI integrated through APIs into applications and processes, testing and monitoring of answers and hallucinations, Python, Git, PyTorch/TensorFlow/scikit-learn, MLOps and cloud deployment. He has shipped a RAG and knowledge-graph pipeline with PII scrubbing, OCR and chunking over a 106,000-document archive at Van den Bosch, built a Copilot Studio and Power Automate assistant handling about 220 tickets a week, and his MSc thesis built a Neo4j and RDF/SPARQL semantic catalogue with a LangChain RAG pipeline and four provenance methods benchmarked. Band: "beloningsbudget tot EUR 7.100 bruto per maand incl. vakantiegeld en mobiliteitsvergoeding" (up to EUR 7,100 gross per month), far above his EUR 4,000 target.

Blocker (hard skip, rule 4(a) Dutch): gates/dutch_gate.py returns exit 10 SKIP_DUTCH_FLUENCY on "Je beheerst de Nederlandse taal uitstekend in woord en geschrift (C1-niveau)" (Dutch at C1 level). Sogeti is a client-facing consultancy working in Dutch at client sites; he is at Dutch A2-B1. No CV, no letter, no form, no email spent, even though the posting names two recruiter addresses (klodin.shahroudi@sogeti.com, danielle.de.vries@sogeti.com): a mail would contradict the rule that a Dutch-fluency requirement is a hard skip. Sogeti Nederland B.V. is on the IND recognised-sponsor register. The posting also notes a PES screening as part of onboarding.

Route: not attempted (hard skip). apply_url: https://nl.linkedin.com/jobs/view/medior-ai-engineer-at-sogeti-4465220731
"""

for slug, text in FITS.items():
    d = os.path.join(APPS, slug)
    p = os.path.join(d, "fit.md")
    open(p, "w", encoding="utf-8").write(text)
    raw = os.path.join(d, "jd-raw.txt")
    if os.path.exists(raw):
        os.remove(raw)
    print(slug, "fit.md", os.path.getsize(p), "bytes | jd.md", os.path.getsize(os.path.join(d, "jd.md")), "bytes")

print("UTC:", subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"], capture_output=True, text=True).stdout.strip())
