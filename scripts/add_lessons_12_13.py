#!/usr/bin/env python3
"""Two more incident lessons from the 23 Sep work, appended to the numbered list in each skill copy."""
import pathlib

TARGETS = [
    "/home/ubuntu/.hermes/skills/productivity/job-application/SKILL.md",
    "/home/ubuntu/.hermes/profiles/vishal/skills/productivity/job-application/SKILL.md",
    "/home/ubuntu/.hermes/profiles/nhung/skills/productivity/job-application/SKILL.md",
]
MARK = "12. **The automation-wording scrub must preserve paragraph structure.**"
ANCHOR_PREFIX = "11. **A sub-agent"
BLOCK = (
    "12. **The automation-wording scrub must preserve paragraph structure.** It split every message on\n"
    "    sentence ends AND newlines and rejoined with a single space, so every employer email arrived as ONE\n"
    "    run-on paragraph even though the draft itself was formatted correctly: the drafts looked fine, the\n"
    "    mail did not. Any text transform on an outgoing message is checked for structure, not just wording.\n"
    "13. **The same discovery query must not be re-issued on every fire.** A sweep issued 92 LinkedIn\n"
    "    guest-API requests per run, serialized and uncached, every 10 minutes from one IP. Discovery goes\n"
    "    through `tools/discovery_cache.py` now (TTL'd, byte-exact body, only a 200 cached, `--offline` for a\n"
    "    cold network): measured 0.42s cold vs 0.08s warm with zero requests, and 80 to 79 `would_fetch` over\n"
    "    the full NL matrix on the second pass.\n"
)

for target in TARGETS:
    p = pathlib.Path(target)
    if not p.is_file():
        print("SKIP", target)
        continue
    text = p.read_text(encoding="utf-8")
    if MARK in text:
        print("already present:", target)
        continue
    lines = text.splitlines()
    start = None
    for i, ln in enumerate(lines):
        if ln.startswith(ANCHOR_PREFIX):
            start = i
            break
    if start is None:
        print("SKIP (no numbered-list anchor):", target)
        continue
    end = start + 1
    while end < len(lines) and lines[end].startswith("    "):
        end += 1
    merged = lines[:end] + BLOCK.rstrip("\n").split("\n") + lines[end:]
    p.write_text("\n".join(merged) + "\n", encoding="utf-8")
    print("updated:", target, len("\n".join(merged)), "chars")
