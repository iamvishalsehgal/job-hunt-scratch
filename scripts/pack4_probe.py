import json, re
base = '/home/ubuntu/.hermes/profiles/vishal/workspace/'
slugs = ['kadaster-data-assetmanager-klic-gia','sia-data-engineer-consultant',
         'advance-in-it-ltd-data-ai-engineer-azure-stack','tata-consultancy-services-l3-azure-cloud-engineer']
p = json.load(open(base + 'route_plan.json'))
print('top:', list(p)[:20] if isinstance(p, dict) else type(p))

def walk(o, path=''):
    if isinstance(o, dict):
        for k, v in o.items():
            if isinstance(v, str) and any(s in v for s in slugs):
                print(path, '|', k, '=', v[:250])
            walk(v, path + '/' + str(k))
    elif isinstance(o, list):
        for v in o:
            walk(v, path)
walk(p)

txt = open('/tmp/register_names.txt', errors='replace').read().splitlines()
for pat in [r'(?i)^sia', r'(?i)sia partners', r'(?i)advance']:
    hits = [l for l in txt if re.search(pat, l)]
    print('PAT', pat, len(hits), hits[:8])
