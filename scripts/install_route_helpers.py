#!/usr/bin/env python3
"""Give Vishal the rest of the route-selection pipeline Nhung runs.

Nhung's workspace has route_test.py (measures what each employer's apply page actually challenges, writing
route_test.json), route_planner.py (turns that evidence into a route per walled row) and accounts.py (the
portal-account store). Vishal's has none of them, which is why his sweep has no evidence-driven route
choice: a walled portal just became Blocked.

This copies each file to <vishal workspace>/ unchanged and verifies it imports and reports its own help.
Usage: install_route_helpers.py <vishal-workspace> [--check-only]
"""
import pathlib
import shutil
import subprocess
import sys

SOURCES = pathlib.Path("/home/ubuntu/.hermes/profiles/nhung/workspace")
FILES = ("route_test.py",)
ADAPTED = ("accounts.py", "route_planner.py")


def main() -> int:
    ws = pathlib.Path(sys.argv[1]).expanduser()
    check_only = "--check-only" in sys.argv
    if not ws.is_dir():
        print(f"no such workspace: {ws}")
        return 2
    planned = []
    for name in FILES:
        src = SOURCES / name
        if not src.is_file():
            print(f"SKIP {name}: not in Nhung's workspace")
            continue
        planned.append((name, src, ws / name))
    for name, src, dest in planned:
        if check_only:
            print(f"would copy {src} -> {dest}")
            continue
        shutil.copy2(src, dest)
        print(f"copied {name} ({dest.stat().st_size} bytes)")
    for name in ADAPTED:
        dest = ws / name
        print(f"{'present' if dest.is_file() else 'MISSING'}: {name}")
    if check_only:
        return 0
    # A helper that cannot even print its help is worse than no helper: the sweep would burn a turn on it.
    for name in ("accounts.py", "route_planner.py", "route_test.py"):
        dest = ws / name
        if not dest.is_file():
            continue
        proc = subprocess.run([sys.executable, str(dest), "--help"], capture_output=True, text=True,
                              timeout=60, cwd=str(ws))
        head = (proc.stdout or proc.stderr).strip().splitlines()[:1]
        print(f"{name}: exit {proc.returncode} | {head[0][:90] if head else '(no output)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
