#!/usr/bin/env python3
"""Owner rule 23 Sep 2026: format the email; never one paragraph.

Adds the shape rule to the job prompt (template + both live stores) and to the playbook file the prompt
points at, then deploys the fixed notify.py (paragraph-preserving scrub) into both workspaces.

Idempotent. Usage: prompt_email_format.py [--apply]
"""
import json
import pathlib
import shutil
import sys
import time

STAMP = time.strftime("%Y%m%d-%H%M%S")
MARK = "### THE EMAIL IS FORMATTED, NEVER ONE PARAGRAPH"

RULE = """
### THE EMAIL IS FORMATTED, NEVER ONE PARAGRAPH (owner rule, 23 Sep 2026)

Every employer email is laid out as an email, not as a blob of prose:

    Dear <Company> recruiting team,          <- greeting, its own line, then a BLANK line

    <one short paragraph answering the posting's first ask>

    <one short paragraph: availability / permit / location, only if the posting raises it>

    Kind regards,                            <- its own line
    <name | email | phone>

- A blank line between every paragraph, the greeting and the sign-off. No paragraph longer than about
  three lines. Never merge the greeting, the body and the signature into one block.
- The attached CV (cv.pdf) and cover letter (cover-letter.pdf) are named in ONE short line, not described.
- The `Wants:` line and any `Recipient:` / `NOT SENT:` meta lines stay in the draft for the tool to strip;
  they are never part of what the employer reads.
- The scrubber that removes automation wording preserves blank lines and paragraph breaks, so a formatted
  draft arrives formatted. If an email ever reads as one paragraph, that is a bug to report, not a style to
  copy.
"""


def patch_prompt_text(p: str) -> tuple[str, bool]:
    if MARK in p:
        return p, False
    anchor = "## THE APPLICATION EMAIL SAYS WHAT THE EMPLOYER ASKED FOR"
    if anchor not in p:
        return p, False
    i = p.index(anchor)
    j = p.find("\n## ", i + len(anchor))
    insert_at = j if j > 0 else len(p)
    return p[:insert_at] + "\n" + RULE + p[insert_at:], True


def main() -> int:
    apply = "--apply" in sys.argv
    print("APPLY" if apply else "DRY RUN")

    # 1. template + both live stores
    targets = [("template", pathlib.Path("/home/ubuntu/jobhunt-agent/engine/cron/jobs.template.json"),
                "{{SLUG}}-job-hunt")]
    for slug in ("vishal", "nhung"):
        targets.append((slug, pathlib.Path(f"/home/ubuntu/.hermes/profiles/{slug}/cron/jobs.json"),
                        f"{slug}-job-hunt"))
    for label, path, jobname in targets:
        data = json.loads(path.read_text(encoding="utf-8"))
        jobs = data if isinstance(data, list) else data["jobs"]
        job = [j for j in jobs if j["name"] == jobname][0]
        new, changed = patch_prompt_text(job["prompt"])
        print(f"  {label}: {len(job['prompt'])} -> {len(new)} chars | changed={changed}")
        if apply and changed:
            shutil.copy2(path, path.with_name(path.name + f".bak-emailformat-{STAMP}"))
            job["prompt"] = new
            tmp = path.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            json.loads(tmp.read_text(encoding="utf-8"))
            tmp.replace(path)

    # 2. the playbook file the prompts point at
    import importlib.util
    spec = importlib.util.spec_from_file_location("pp", "/home/ubuntu/jobhunt-agent/engine/tools/prompt_playbook.py")
    pp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pp)
    tpl = json.loads(pathlib.Path("/home/ubuntu/jobhunt-agent/engine/cron/jobs.template.json").read_text(encoding="utf-8"))
    tpl = tpl if isinstance(tpl, list) else tpl["jobs"]
    prompt = [j for j in tpl if j["name"] == "{{SLUG}}-job-hunt"][0]["prompt"]
    for heading, chunk in pp.sections(prompt):
        entry = pp.entry_for(heading)
        if not entry or "email" not in (getattr(entry, "file", "") or ""):
            continue
        print(f"  playbook entry for {heading[:40]}: {getattr(entry, 'file', '')}")

    # 3. deploy the fixed scrubber to both workspaces
    src = pathlib.Path("/home/ubuntu/jobhunt-agent/engine/notify/notify.py").read_text(encoding="utf-8")
    for slug in ("vishal", "nhung"):
        dest = pathlib.Path(f"/home/ubuntu/.hermes/profiles/{slug}/workspace/tools/notify.py")
        if not dest.is_file():
            print(f"  {slug}: no tools/notify.py - skipped")
            continue
        same = dest.read_text(encoding="utf-8") == src
        print(f"  {slug}: tools/notify.py identical={same}")
        if apply and not same:
            shutil.copy2(dest, dest.with_name(dest.name + f".bak-paragraphs-{STAMP}"))
            dest.write_text(src, encoding="utf-8")
            print(f"  {slug}: deployed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
