import json
import subprocess

fields = [
    "tronox-principal-data-governance",
    "submitted",
    "ApplicantStack confirmation page after Submit: title 'Application Received - Tronox', body 'Thank you for your application. We will review your information and contact you if you match our requirements.' at https://tronox.applicantstack.com/x/apply/a22jku1zoc30 (no captcha/challenge)",
    "Board-live verified on Tronox own ApplicantStack board (GET /x/openings HTTP 200, 4 Principal Data Governance rows incl. NLD - Botlek) and detail /x/detail/a22jku1zoc30 HTTP 200 = ID 40081739, Job Location NLD - Botlek, Job Function Information Technology. Gates on company-board JD: dutch_gate OK (no Dutch requirement, English JD), eu_scope OK NL, row_gate NO_ROW (netherlands, no publish gate). IND work register (fetched live, 2026-09-20) lists Tronox Pigments (Holland) B.V. 24179173, Tronox International B.V. 67086497, Tronox Investments Netherlands B.V. 56102259. Screening questions answered accurately, not optimistically: Q1 degree = Yes with explanation (Advanced LL.M. Law & Digital Technologies Leiden on LL.B. Hanoi Law), enterprise data governance programme / decision-rights stewardship / data quality frameworks / governance-platform (catalogue, lineage) / SAP S4HANA-Databricks experience = No, certifications free text = none of DCAM/CDMP/DAMA/SAP MDG/TOGAF/COBIT/CISA/CGEIT, IAPP AIGP in preparation. Fit 3/5 (seniority not a blocker; core governance/documentation/stakeholder work transferable). ApplicantStack resume parser overwrote First/Last name (became 'Nhung Trang'/'Giap') and blanked Address 1/City/State/Zip; refilled correct values before submitting. Visa stated as zoekjaar now, HSM sponsor needed later.",
    "nhung-2026-cv.pdf (66,349 B), nhung-2026-cover-letter.pdf (19,322 B); cover letter text also pasted into the form's Cover Letter box",
    "/home/ubuntu/Desktop/job-hunt-nhung/applications/tronox-principal-data-governance/jd.md",
    "https://tronox.applicantstack.com/x/apply/a22jku1zoc30",
    "applicantstack-ats",
    "2026-09-20T06:36:06Z",
]
print(json.dumps(fields))
with open("/home/ubuntu/job-hunt-scratch/result_fields.json", "w") as fh:
    json.dump(fields, fh)
