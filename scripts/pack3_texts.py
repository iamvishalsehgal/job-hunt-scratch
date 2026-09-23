#!/usr/bin/env python3
"""Write the text files for pack batch 3 (roles 9-12). Cron-safe: no pipes, no /tmp."""
import json
import pathlib

WS = pathlib.Path("/home/ubuntu/.hermes/profiles/vishal/workspace")
APPS = WS / "applications"

FARM_JD = """# Business Intelligence Engineer - Farm Frites (South Holland)

Source: https://nl.linkedin.com/jobs/view/business-intelligence-engineer-at-farm-frites-4445741767
Posted: 1 week ago | 85 applicants

Jij vertaalt data naar strategie en resultaat. Met jouw passie voor data, analytics en datamodellering
vertaal je complexe vraagstukken naar heldere inzichten en slimme oplossingen. Je doorgrondt
informatiestromen, ontdekt verbetermogelijkheden en helpt de organisatie beter te sturen op feiten.
Of het nu gaat om klantwinstgevendheid, supply chain-optimalisatie of innovatieve datagedreven
oplossingen, jij zorgt ervoor dat data leidt tot betere beslissingen en tastbare resultaten.

Wat je gaat doen:
- Slim omzetten en structureren van data naar verantwoordings- en stuurinformatie;
- Adviseren omtrent continue verbetering en optimalisatie van ons datawarehouse
- Aandragen van inzichten in user stories en testscenario's (agile/scrum)
- Informatiebehoeften vertalen naar gewenste rapportages;
- Meedenken over de volgende stappen in onze data/IT-strategie

Wat breng je mee als Business Intelligence Engineer?
- HBO werk- en denkniveau, bij voorkeur in IT of bedrijfskunde
- Minimaal 5 jaar ervaring in Business Intelligence Engineer of vergelijkbare rol
- Aantoonbare kennis/ervaring met BI tooling; (extra certificaten zijn een plus)
- Uitstekende communicatieve vaardigheden in Nederlands en Engels
- Analytisch sterk, proactief en klantgericht. Je bent een echte teamplayer!

Wat biedt Farm Frites?
- Salaris tussen EUR 4.725 en EUR 6.938 bruto per maand (Farm Frites CAO, schaal 9 bij 40 uur per week)
- Internationale familiebedrijf in de agri-food sector, moderne applicatielandschap in aanbouw
"""

FARM_FIT = """# fit - farm-frites-business-intelligence-engineer

Fit: 3.9/5 technically, but OUTCOME IS SKIP: hard-skip rule (a), explicit Dutch-fluency requirement.

Why: The work itself matches - structuring data into management reporting, improving a datawarehouse,
translating information needs into reporting, agile/scrum user stories - and he has done all four:
a real-time BI dashboard suite (sales, stock turnover, margin) at Veena Boutique, Power BI with
advanced DAX as his reporting layer, and a SQL Server Data Vault 2.0 warehouse at Van den Bosch
Transporten. Posted salary EUR 4,725 to 6,938 gross per month clears both his EUR 3,300 floor and
his EUR 4,400 ask.

Hard skip reason: the posting's requirements list "Uitstekende communicatieve vaardigheden in
Nederlands en Engels" - excellent communication in Dutch AND English. That is an explicit
Dutch-fluency requirement, i.e. PACK_RULES 4(a) HARD SKIP. His Dutch is beginner level, so he
cannot compete in a Dutch-language BI role that asks for excellent Dutch communication with
business stakeholders.

Secondary blockers (recorded, not decisive):
- Minimum 5 years in a BI Engineer or comparable role. Not met as a dedicated BI title: he has
  enterprise BI/reporting work from 2026 to date plus the Veena Boutique BI period.
- Salary is inside range, so salary is not the reason for the skip.

IND: Farm Frites International B.V. is on the IND recognised-sponsor register, so the employer
itself would have been eligible - the language requirement is the only blocker.

Route: none - skipped, no pack PDFs, no email.
"""

MOM_JD = """# Agentic AI Developer - Momentum (Amsterdam)

Source: https://nl.linkedin.com/jobs/view/agentic-ai-developer-at-momentum-4448535174
Posted: 2 weeks ago | 126 applicants | Momentum Digital

Momentum Digital is een snelgroeiend bedrijf dat organisaties helpt hun digitale ambities te
realiseren. We combineren strategie, technologie en uitvoering. Om onze groei te ondersteunen zijn
we op zoek naar een Junior Agentic AI Developer.

Jouw nieuwe rol
Als Medior Software Engineer bij Momentum Digital lever je digitale transformatieprojecten die
meetbare bedrijfswaarde creeren. Je ontwerpt en bouwt slimme, schaalbare, data-gedreven
oplossingen, van AI-aangedreven workflows en autonome agents tot geavanceerde analytics-toepassingen
- met gebruik van technologieen zoals Python (Django), Azure cloud-native services, Terraform,
GitHub (CI/CD), Cursor AI, Tailwind en Large Language Models.

Competencies
- In het bezit van professionele Databricks-certificeringen voor Data Engineering en Machine Learning.
- Aantoonbare sterke expertise in het ontwikkelen van data-gedreven applicaties met Python, met
  praktische ervaring in Azure en het implementeren van oplossingen die gebruikmaken van Large
  Language Models.
- In het bezit van een afgeronde hbo- of masteropleiding, bij voorkeur in een wetenschappelijke richting.
- Vloeiend in het Nederlands, met uitstekende klantinteractie- en presentatievaardigheden, in staat
  om effectieve gesprekken te leiden.
- Bewezen vermogen tot samenwerking in teamverband en het aanpakken van complexe vraagstukken.

Verantwoordelijkheden: minimaal 90% van de projecten op tijd en binnen budget; Net Promoter Score
van 50 of hoger; circa 10% van de tijd aan persoonlijke ontwikkeling.
"""

MOM_FIT = """# fit - momentum-agentic-ai-developer

Fit: 4.1/5 technically, but OUTCOME IS SKIP: hard-skip rule (a), explicit Dutch-fluency requirement.

Why: The technical core - Python, Azure cloud-native services, LLM-backed solutions, autonomous
agents - is close to what he delivers today: a RAG and knowledge-graph pipeline with PII scrubbing,
OCR and chunking over a 106,000-document archive, a Copilot Studio service-desk assistant handling
about 220 tickets a week, and Azure APIM, Functions and Data Factory in production. His MSc thesis
built a semantic catalogue over Neo4j with RDF/SPARQL.

Hard skip reason: the competency list states "Vloeiend in het Nederlands" (fluent in Dutch) with
client-facing presentation duties. That is an explicit Dutch-fluency requirement, PACK_RULES 4(a)
HARD SKIP. His Dutch is beginner level, and the role is client-facing for a consultancy.

Secondary blockers (recorded, not decisive):
- Databricks professional certifications for Data Engineering and Machine Learning are listed as a
  competency he must hold. He has Databricks exposure but does not hold those certifications.
- The advert also names a Junior Agentic AI Developer while the role title is Medior Software
  Engineer, so the seniority band is unclear.
- No salary figure is published in the posting, so the salary rule cannot be evaluated either way.

IND: no entity on the register matches this "Momentum" (Momentum Digital, Amsterdam). The only
register hit is Stichting GGZ Momentum, an unrelated care organisation, so the employer is not
confirmed as a recognised sponsor either. With the Dutch requirement this is a double blocker.

Route: none - skipped, no pack PDFs, no email.
"""

ILIONX_JD = """# AI Engineer - ilionx (Data & AI, 's-Hertogenbosch / Amersfoort)

Source: https://nl.linkedin.com/jobs/view/ai-engineer-at-ilionx-4429349827
Own board: https://werkenbij.ilionx.com/vacatures/ai-engineer-5734477
Posted: 1 week ago | 200+ applicants | Recruiter: Bram Wiggers (Recruitment Business Partner, ilionx)

Van slimme chatbots tot geavanceerde LLM-oplossingen: bij ilionx bouw je aan AI-toepassingen die
ertoe doen.

Jouw nieuwe functie als AI Engineer
Vanuit ons kantoor in Den Bosch werk je als AI Engineer aan het praktisch en schaalbaar toepassen
van AI bij onze klanten. Je bouwt niet alleen slimme oplossingen, je helpt organisaties ook echt
vooruit: meedenken met de klant, de juiste vragen stellen, kansen signaleren en AI vertalen naar
concrete bedrijfswaarde.

Je werkt aan innovatieve AI-oplossingen met bewezen impact: het ondersteunen van besluitvorming met
machine learning (human-in-the-loop), het automatiseren van bedrijfsprocessen, en het ontwikkelen
van generatieve AI-oplossingen met LLM's en agents. Je integreert taal-, beeld- en multimodale
modellen naadloos in bestaande bedrijfsprocessen en IT-landschappen.

Daarnaast bouw je aan slimme chatbots, co-pilots en agent-based systemen die gebruikers ondersteunen
en processen versnellen. Je weet hoe je met prompt engineering het maximale uit LLM's haalt en hoe
je generatieve AI koppelt aan interne en externe kennisbronnen met technieken als RAG, vector search
en tool calling.

Je schakelt moeiteloos tussen techniek en toepassing. Samen met data engineers, data scientists en
cloudspecialisten werk je aan oplossingen die niet in de la verdwijnen, maar daadwerkelijk in
productie draaien. Je ontwerpt mee aan robuuste AI-architecturen en denkt mee over system- en
solution design: van probleemdefinitie tot eerste schets en uiteindelijke implementatie.

Je werkt met de AI-offeringen van grote public cloud providers (zoals Azure, AWS of GCP) en maakt
gebruik van moderne frameworks en tooling zoals LangChain, dSPy, PydanticAI, n8n en MCP. Platforms
als Databricks zijn daarbij een pre, geen must.

Wat ons onderscheidt: we zoeken hyperdevelopers. Engineers die zelf dagelijks LLM's en agents
inzetten om slimmer en sneller te werken, en die hun kennis actief delen met collega's en klanten.

Wat bieden wij jou:
- Salaris tussen de EUR 4.500 en EUR 7.000 o.b.v. 40 uur, plus bonussysteem
- Volledig hybride werken: bij de klant, op kantoor of vanuit huis
- Veel ruimte voor initiatief, innovatie en experimenteren
- Een persoonlijk loopbaantraject (technisch, inhoudelijk of richting consultancy/architectuur)
- Samenwerking met gedreven collega's uit verschillende specialismen binnen Data, AI en Cloud

Wat vragen wij van jou:
- Aantoonbare ervaring met het ontwikkelen, implementeren en productierijp maken van AI-oplossingen
- Ervaring met LLM's, prompt engineering en agent-based toepassingen
- Ervaring met de AI-offeringen van grote public cloud providers
- Je hebt meegebouwd aan AI-oplossingen zoals chatbots, co-pilots, classifiers, recommender systems
  of vergelijkbare toepassingen
- Senioriteit: Medior / Senior, technology area Data & AI
"""

ILIONX_FIT = """# fit - ilionx-ai-engineer

Fit: 4.0/5

Why: The advert asks for production AI, not demos: LLM and agent solutions, RAG, vector search,
tool calling, prompt engineering, integrated with existing business processes and IT landscapes.
That is his current work. At Van den Bosch Transporten he built a service-desk assistant over a
19,084-ticket / 106,000-document knowledge base (Copilot Studio plus Power Automate, about 220
tickets a week) and a RAG plus knowledge-graph pipeline with PII scrubbing, OCR and chunking, and
his MSc thesis built a semantic catalogue over Neo4j and RDF/SPARQL with a Gemini plus LangChain RAG
pipeline and four provenance methods benchmarked. Modern frameworks listed include LangChain, which
he uses, plus MCP and PydanticAI, both adjacent to his MCP/tool-calling exposure.

Gaps / blockers:
- Salary: EUR 4,500 to 7,000 gross per month at 40 hours, plus bonus. This clears his EUR 3,300
  floor and his EUR 4,400 ask with room, so quote EUR 4,400 to 5,000 gross base if a field demands
  a figure; never below EUR 4,000.
- No Dutch-fluency requirement appears in the posting. It is written in Dutch (dutch_gate verdict
  recorded in the pack), and the role is client-facing consultancy, so confirm the working language
  of the Data & AI unit in the first call.
- dSPy, PydanticAI, n8n and Databricks-as-a-platform are not yet in his production stack; LangChain,
  RAG, vector search and tool calling are. Nothing in the pack claims otherwise.
- Frameworks and platforms are a pre, not a must, for Databricks, so no claim is made on it.
- Visa: HSM permit to 3 Dec 2026. ilionx's legal entity on the IND register is IlionX Group B.V.
  (register line 5418), so a transfer is possible; his MSc (awarded 28 Nov 2025) also keeps him
  inside the reduced-salary criterion.
- Location: the pack is for the Data & AI AI Engineer vacancy in 's-Hertogenbosch (Amersfoort is the
  LinkedIn location tag and an ilionx office base); commute from 's-Hertogenbosch home is local.

Route: ilionx own careers board, werkenbij.ilionx.com vacancy 5734477 (apply form), email fallback
prepared.
"""

ILIONX_TAILOR = {
    "headline": "Vishal Sehgal",
    "summary": (
        "AI engineer and data engineer with a WO Master in Data Science (TU Eindhoven with Tilburg "
        "University, JADS, awarded 28 November 2025). I build LLM and agent solutions that reach "
        "production: a service-desk assistant over a 19,084-ticket and 106,000-document knowledge base "
        "at about 220 tickets a week, and a RAG plus knowledge-graph pipeline with PII scrubbing, OCR "
        "and chunking. My MSc thesis built a semantic catalogue over Neo4j and RDF/SPARQL with a "
        "LangChain RAG pipeline and four provenance methods benchmarked. I work in Azure daily "
        "(Fabric, APIM, Functions, Data Factory) alongside Python, SQL Server and Data Vault 2.0."
    ),
    "skills": [
        {"name": "Generative AI & LLM Engineering",
         "entries": "LLM applications, RAG (hybrid retrieval, cross-encoder reranking), prompt engineering, tool calling, agents, LangChain, GraphRAG, provenance and attribution methods, Neo4j, RDF/SPARQL"},
        {"name": "AI Integration & Production",
         "entries": "Copilot Studio, Power Automate, Azure APIM, Azure Functions, Azure Data Factory, API and subscription-key auth, Key Vault, human-in-the-loop decision support"},
        {"name": "Cloud (Azure, GCP, AWS)",
         "entries": "Azure (Fabric, APIM, Functions, Data Factory), GCP (Cloud Run, Pub/Sub, BigQuery, Build), AWS S3, Docker"},
        {"name": "Data Engineering & Big Data",
         "entries": "Python, SQL, PySpark, Apache Kafka, Spark Structured Streaming, Snowflake, BigQuery, Databricks (project and coursework exposure), dbt"},
        {"name": "Machine Learning & NLP",
         "entries": "Scikit-learn, TensorFlow, PyTorch, XGBoost, BERT, BERTopic, TF-IDF, Word2Vec, classification and recommender systems, genetic algorithms (DEAP)"},
        {"name": "Databases & Modelling",
         "entries": "SQL Server, Data Vault 2.0, temporal tables, PostgreSQL, Oracle, MySQL, semantic and entity modelling"},
        {"name": "Reporting & Visualisation",
         "entries": "Power BI (advanced DAX), Excel, Dash, Plotly, React"},
        {"name": "Practices",
         "entries": "Git and GitLab CI/CD, Agile and Scrum, JIRA, stakeholder-facing solution design"},
    ],
    "projects": [
        {"name": "Semantic Cataloging of AI Models (MSc thesis)",
         "desc": "Neo4j and RDF/SPARQL knowledge base built from Hugging Face model cards, Gemini plus LangChain RAG pipeline, four provenance and attribution methods benchmarked for answer accuracy."},
        {"name": "RAG Me Up",
         "desc": "Modular RAG with hybrid retrieval (Milvus and pgvector plus BM25), cross-encoder reranking, provenance tracking and GraphRAG (NetworkX and LangChain)."},
        {"name": "Service-desk AI assistant (Van den Bosch)",
         "desc": "Copilot Studio plus Power Automate assistant over 19,084 tickets and 106,000 documents, handling about 220 tickets a week."},
        {"name": "End-to-End MLOps (Stroke Prediction)",
         "desc": "Vertex AI pipelines, champion-challenger model selection, Flask API and UI on Cloud Run."},
        {"name": "Scalable NBA Data Architecture (GCP)",
         "desc": "Spark cluster plus Kafka streaming and PySpark batch ETL."},
    ],
}

ILIONX_LETTER = """Vishal Sehgal
Uilenburg 5G, 5211 EV 's-Hertogenbosch, Netherlands
vishalsehgal414@gmail.com | +31 6 10159758
linkedin.com/in/iamvishalsehgal | github.com/iamvishalsehgal

Dear ilionx Data & AI team,

I am applying for the AI Engineer role in your Data & AI technology area. Building AI that runs in
production rather than in a deck is what my current work is: at Van den Bosch Transporten I built a
service-desk assistant over a 19,084-ticket and 106,000-document knowledge base that handles about
220 tickets a week, and a RAG plus knowledge-graph pipeline with PII scrubbing, OCR and chunking
feeding it.

Your advert names RAG, vector search, tool calling and prompt engineering, plus generative AI with
LLM's and agents integrated into existing processes. That is exactly the ground my MSc thesis and my
side work cover: a semantic catalogue over Neo4j and RDF/SPARQL, a Gemini plus LangChain RAG
pipeline, and four provenance and attribution methods benchmarked for answer accuracy. RAG Me Up,
my modular RAG project, pairs hybrid retrieval (vectors plus BM25) with cross-encoder reranking. On
the platform side I work in Azure daily: Fabric, APIM, Functions and Data Factory, with Python, SQL
Server and Data Vault 2.0 under them.

I am based in 's-Hertogenbosch, so the Den Bosch office is local to me, and I would enjoy the mix of
client work and building that ilionx describes. I hold a Highly Skilled Migrant permit valid to
3 December 2026 and a WO Master from TU Eindhoven with Tilburg University (JADS, awarded 28 November
2025); IlionX Group B.V. is on the IND recognised-sponsor register, so a transfer is
straightforward. My current role is a fixed seven-month contract, 4 May to 3 December 2026, ending
by its own terms, and I can start on short notice.

Kind regards,
Vishal Sehgal
"""

ILIONX_MAIL = """Subject: Application for AI Engineer (Data & AI, 's-Hertogenbosch) - Vishal Sehgal

Recipient: Bram Wiggers, Recruitment Business Partner, ilionx (named on the vacancy as the poster;
no personal address published - [HR-EMAIL] none-found, the board apply form is the primary route).

Dear Bram Wiggers,

I would like to apply for the AI Engineer role in the Data & AI technology area.

I am an AI and data engineer with a WO Master in Data Science from TU Eindhoven with Tilburg
University (JADS, awarded 28 November 2025). At Van den Bosch Transporten I built a service-desk
assistant over a 19,084-ticket and 106,000-document knowledge base, handling about 220 tickets a
week, on top of a RAG plus knowledge-graph pipeline with PII scrubbing, OCR and chunking. My MSc
thesis built a semantic catalogue over Neo4j and RDF/SPARQL with a LangChain RAG pipeline and four
provenance methods benchmarked for answer accuracy.

Your advert asks for LLM's, prompt engineering, agent-based applications and production AI on the
major public clouds. Those are the tools I work in daily: Azure Fabric, APIM, Functions and Data
Factory, plus Python, SQL Server and Data Vault 2.0. I am based in 's-Hertogenbosch, so the Den
Bosch office is local.

I hold a Highly Skilled Migrant permit valid to 3 December 2026; IlionX Group B.V. is on the IND
recognised-sponsor register, so a transfer is possible. My current role is a fixed seven-month
contract, 4 May to 3 December 2026, ending by its own terms, and I can start on short notice.
Expected gross base: EUR 4,400 to 5,000 per month.

Attachments: cv.pdf, cover-letter.pdf.

Kind regards,
Vishal Sehgal
Uilenburg 5G, 5211 EV 's-Hertogenbosch, Netherlands
vishalsegblehgal414@gmail.com
"""

ILIONX_MAIL = ILIONX_MAIL.replace("vishalsegblehgal414@gmail.com",
                                  "vishalsehgal414@gmail.com | +31 6 10159758\nlinkedin.com/in/iamvishalsehgal")


def write(slug, files):
    d = APPS / slug
    d.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        if name.endswith(".json"):
            (d / name).write_text(json.dumps(content, indent=2, ensure_ascii=False) + "\n")
        else:
            (d / name).write_text(content if content.endswith("\n") else content + "\n")
    return sorted(files)


if __name__ == "__main__":
    w1 = write("ilionx-ai-engineer", {
        "jd.md": ILIONX_JD, "fit.md": ILIONX_FIT, "tailoring.json": ILIONX_TAILOR,
        "cover-letter.md": ILIONX_LETTER, "email-to-hr.md": ILIONX_MAIL,
        "apply-url.txt": "https://werkenbij.ilionx.com/vacatures/ai-engineer-5734477\n",
    })
    w2 = write("farm-frites-business-intelligence-engineer", {"jd.md": FARM_JD, "fit.md": FARM_FIT})
    w3 = write("momentum-agentic-ai-developer", {"jd.md": MOM_JD, "fit.md": MOM_FIT})
    print("ilionx-ai-engineer", w1)
    print("farm-frites", w2)
    print("momentum", w3)
