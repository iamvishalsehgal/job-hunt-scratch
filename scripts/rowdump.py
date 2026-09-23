import ast, pathlib, sys
p = pathlib.Path('/home/ubuntu/.hermes/profiles/vishal/workspace/build_tracker.py')
src = p.read_text(encoding='utf-8')
tree = ast.parse(src)
rows = None
for node in ast.walk(tree):
    if isinstance(node, ast.Assign) and getattr(node.targets[0], 'id', '') == 'applications':
        rows = ast.literal_eval(node.value)
want = set(sys.argv[1:])
for r in rows:
    if str(r[0]) in want:
        print(f"#{r[0]} | {r[1]} | {r[2]} | {r[3]} | status={r[5]} | ats={r[6]} | url={r[10]}")
        print(f"   NOTE: {str(r[11])[:700]}")
