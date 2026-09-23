import os
B = '/home/ubuntu/.hermes/profiles/vishal/workspace/'
slugs = ['kadaster-data-assetmanager-klic-gia', 'sia-data-engineer-consultant',
         'advance-in-it-ltd-data-ai-engineer-azure-stack',
         'tata-consultancy-services-l3-azure-cloud-engineer']
for s in slugs:
    p = B + 'applications/' + s + '/jd.md'
    t = open(p, encoding='utf-8').read()
    n = t.count('\u2014') + t.count('\u2013')
    t = t.replace('\u2014', '-').replace('\u2013', '-')
    open(p, 'w', encoding='utf-8').write(t)
    print(p, 'replaced', n, 'chars, bytes', os.path.getsize(p))
