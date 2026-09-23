#!/usr/bin/env python3
"""Patch the same two skill lessons on a remote host, where the edits cannot be made locally.

This exists because the laptop no longer holds a copy of any VM file - the patcher is streamed to the VM
and run there, rather than staged on the operator's machine and copied across.
"""
import pathlib

OLD_FALLBACK = (
    "- **If the VM is down and he still wants a deliverable, you can send it from the Mac.** A read-only copy of the bot token lives in `~/.hermes/.env.bak-*`. `sendMessage` / `sendDocument` are stateless, so a one-off send from the Mac works - but NEVER call `getUpdates` from there, because polling is what claims the update stream and it breaks the VM gateway when it comes back. Recovery for a wedged VM (SSH `banner exchange` timeouts, Run Command stuck in `ACCEPTED`) is in the `oracle-cloud-hosting` skill's `references/hermes-on-arm-vm.md`."
)
NEW_FALLBACK = (
    "- **The VM is the only host, and it holds the only bot token.** Owner rule, 23 Sep 2026: the Oracle VM is fully separated from the operator's laptop, which now holds no copy of the job-hunt tree, no candidate workspace and no bot token. Work on the VM, keep scratch in `~/job-hunt-scratch/`, and never recreate a laptop-side copy of a file that belongs here. A wedged VM is recovered, not worked around (SSH `banner exchange` timeouts, Run Command stuck in `ACCEPTED`) - see the `oracle-cloud-hosting` skill's `references/hermes-on-arm-vm.md`."
)
OLD_HOST = (
    "- **Identify the host before reasoning about what \"should\" exist.** The job-hunt tree is a synced copy of the Mac project, so Mac-only artifacts (`.DS_Store`, `._*` AppleDouble sidecars) and the Mac-path hardcode in `build_tracker.py` are NOT evidence you are on the Mac. Check with `hostname; uname -m; curl -s https://api.ipify.org` first. On the Oracle VM, an attempt to ssh \"to the VM\" is refused because you are already on it (`~/.oci` and the VM ssh key live on the Mac only)."
)
NEW_HOST = (
    "- **Identify the host before reasoning about what \"should\" exist.** The job-hunt tree exists in ONE place - this VM - so nothing about it is evidence about the host; `.DS_Store` and `._*` AppleDouble sidecars are legacy artifacts of the retired laptop copy. Check with `hostname; uname -m; curl -s https://api.ipify.org` first. Here, an attempt to ssh \"to the VM\" is refused because you are already on it (the `~/.oci` credentials and the ssh key live with the operator, out of scope for this work)."
)
TARGETS = (
    "/home/ubuntu/.hermes/skills/productivity/job-application/SKILL.md",
    "/home/ubuntu/.hermes/profiles/vishal/skills/productivity/job-application/SKILL.md",
    "/home/ubuntu/.hermes/profiles/nhung/skills/productivity/job-application/SKILL.md",
)


def main() -> int:
    for target in TARGETS:
        p = pathlib.Path(target)
        if not p.is_file():
            print(f"SKIP {target}: not a file")
            continue
        text = original = p.read_text(encoding="utf-8")
        if OLD_FALLBACK in text:
            text = text.replace(OLD_FALLBACK, NEW_FALLBACK)
        elif "- **If the VM is down and he still wants a deliverable" in text:
            start = text.index("- **If the VM is down and he still wants a deliverable")
            text = text[:start] + NEW_FALLBACK + text[text.index("\n", start):]
        if OLD_HOST in text:
            text = text.replace(OLD_HOST, NEW_HOST)
        elif "- **Identify the host before reasoning" in text:
            start = text.index("- **Identify the host before reasoning")
            text = text[:start] + NEW_HOST + text[text.index("\n", start):]
        if text == original:
            print(f"SKIP {target}: already patched")
            continue
        p.write_text(text, encoding="utf-8")
        stale = [m for m in ("send it from the Mac", "synced copy of the Mac project",
                             ".env.bak-*") if m in text]
        print(f"patched {target} ({len(original)} -> {len(text)} chars) | stale left: {stale or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
