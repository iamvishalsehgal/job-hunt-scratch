import os
WS = "/home/ubuntu/.hermes/profiles/vishal/workspace/applications"
for slug in ["haskoning-bi-consultant-asset-management",
             "deloitte-junior-engineer-next-generation-customer-solutions"]:
    p = os.path.join(WS, slug, "jd.md")
    t = open(p, encoding="utf-8").read()
    n = t.count("\u2014")
    open(p, "w", encoding="utf-8").write(t.replace("\u2014", " - "))
    print(slug, "em-dashes replaced:", n)
