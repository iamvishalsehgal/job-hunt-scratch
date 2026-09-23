import os
B = '/home/ubuntu/.hermes/profiles/vishal/workspace/applications/'

files = {
 'kadaster-data-assetmanager-klic-gia/fit.md': """# Fit - Data Assetmanager KLIC & GIA, Kadaster (Apeldoorn)

fit: 3.7/5

- Data governance / data asset role, adjacent to his SQL Server Data Vault 2.0 warehouse, the 704-process ETL audit and the RAG plus knowledge-graph work; his MSc thesis (Neo4j, RDF/SPARQL semantic catalogue) maps onto the data modelling duties.
- Pay: EUR 5.503,58 - 7.150,01 per month (schaal 12, 36h) plus up to EUR 1.787,50 IKB. Clears the EUR 3.300 floor and the EUR 4.000 ask.
- Kadaster is on the IND register of recognised sponsors (register line 6025), so an HSM transfer is possible.

blockers:
- gates/dutch_gate.py: SKIP_DUTCH_LANGUAGE, posting written in Dutch (24 Dutch markers, 3.73 per 1k chars). The capture holds no explicit "Dutch fluency required" sentence, so this is the gate heuristic, not a stated requirement: the parent can override and re-queue at no cost.
- Public-body data management role (Wibon/KLIC legislation) rather than a data-engineering build role. No CV, letter or email spent.
""",
 'sia-data-engineer-consultant/fit.md': """# Fit - Data Engineer Consultant, Sia (Amsterdam)

fit: 3.7/5

- Technical match is close: Python and SQL data engineering, GCP (BigQuery, Pub/Sub, Cloud Run), Docker, GitLab CI/CD, plus Azure APIM/Functions and IaC-adjacent automation.
- Consultancy model can work for an HSM transfer: Sia Partners is on the IND register.
- Pay not published on the posting, so no band check was possible.

blockers:
- Hard skip 4(a) Dutch fluency, verbatim: "Excellent English and Dutch verbal and written skills are required" and "Non-Dutch speaker will no be accepted".
- Hard skip 4(b) sponsorship: "Unfortunately, we are unable to provide a work permit for this position".
- No CV, letter or email spent.
""",
 'advance-in-it-ltd-data-ai-engineer-azure-stack/fit.md': """# Fit - Data & AI engineer (Azure stack), Advance in IT Ltd (Amsterdam)

fit: 3.6/5

- Azure Fabric, APIM, Functions, Data Factory, SQL Server plus RAG/knowledge-graph experience lines up with the Azure and AI stack described.
- Posted pay: EUR 6.500 to 10.000 package (base plus bonus plus car allowance). Clears the EUR 3.300 floor and the EUR 4.000 ask.
- Permanent contract from the outset is advertised.

blockers:
- Agency posting: Advance in IT Ltd is a UK IT staffing firm advertising on behalf of an unnamed 23-person Amsterdam data/AI consultancy ("this 23-person specialist Data, AI & Cloud consultancy"), so the employing legal entity is not identified.
- Advance in IT Ltd is not on the IND register of recognised sponsors (no matching entry in the register name list), and an agency cannot sponsor an HSM transfer. Hard skip rule 4(c) plus the agency rule: no CV may go out before a registered end client is named.
- No CV, letter or email spent.
""",
 'tata-consultancy-services-l3-azure-cloud-engineer/fit.md': """# Fit - L3 Azure Cloud Engineer, Tata Consultancy Services (The Hague)

fit: 3.5/5

- Azure platform work (APIM, Functions, Data Factory, Key Vault, subscription-key auth) and integration troubleshooting (Seeburger to APIM to Function routing) is adjacent to the L3 Azure operations scope.
- TCS Netherlands B.V. is on the IND register (line 11065), so an HSM transfer is possible.
- Pay not published on the posting, so no band check was possible.

blockers:
- Hard skip 4(a) Dutch fluency, verbatim: "Uitstekende beheersing van de Nederlandse taal en goede beheersing van de Engelse taal".
- Scope is Azure cloud operations and IaC (Bicep, Terraform, Entra ID, backup, DR) rather than data engineering, at L3 operations depth. No materials spent.
""",
}

for slug in ['kadaster-data-assetmanager-klic-gia', 'sia-data-engineer-consultant',
             'advance-in-it-ltd-data-ai-engineer-azure-stack',
             'tata-consultancy-services-l3-azure-cloud-engineer']:
    d = B + slug + '/'
    os.makedirs(d, exist_ok=True)
    open(d + 'apply-url.txt', 'w').write('linkedin-easy-apply-only\n')

for rel, txt in files.items():
    p = B + rel
    assert '\u2014' not in txt and '\u2013' not in txt
    open(p, 'w').write(txt)

for rel in list(files) + ['kadaster-data-assetmanager-klic-gia/apply-url.txt']:
    p = B + rel
    print(p, os.path.getsize(p))
