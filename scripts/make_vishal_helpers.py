#!/usr/bin/env python3
"""Build Vishal's copies of Nhung's two pipeline helpers from her own files.

Only identity/paths change: the storage vault, the login email, the shared portal password and the
workspace base. Every decision rule is left exactly as Nhung's proven file has it, so the two candidates
run the same pipeline mechanics.

Usage: make_vishal_helpers.py <n-accounts.py> <n-route_planner.py> <n-route_test.py> <out-dir>
"""
import pathlib
import re
import sys

PORTAL_PASSWORD = "ApplicationPortal0"
CANDIDATE = "Vishal"
EMAIL = "vishalsehgal414@gmail.com"
VAULT = "/home/ubuntu/.hermes/profiles/vishal/vault"
BASE = "/home/ubuntu/.hermes/profiles/vishal/workspace"

WORDS = (("Nhung", CANDIDATE), ("nhung", CANDIDATE.lower()))


def reword(text: str) -> str:
    """Nhung's prose, in Vishal's words.

    Long phrases first, and the pronouns are only rewritten inside those phrases: a bare `her` -> `his`
    would corrupt ordinary words (`other`, `there`), and the prose that matters is covered by the phrases.
    """
    for phrase, replacement in (("their real details", "his real details"),
                                ("with her real details", "with his real details"),
                                ("her real details", "his real details"),
                                ("needs her (NL only)", "needs Vishal (NL only)"),
                                ("Needs Nhung (Netherlands only)", "Needs Vishal (Netherlands only)"),
                                ("her mailbox", "his mailbox"),
                                ("Her browser", "His browser"),
                                ("she could not log back in", "he could not log back in"),
                                ("for her (same convention", "for him (same convention"),
                                ("Scope rules (Nhung,", "Scope rules (Vishal,"),
                                ("in her\n                        campaign", "in his\n                        campaign"),
                                ("her campaign", "his campaign"),
                                ("18 of her hard bounces", "18 hard bounces")):
        text = text.replace(phrase, replacement)
    for word, replacement in WORDS:
        text = re.sub(rf"\b{word}\b", replacement, text)
    return text


def main() -> int:
    src_accounts = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
    src_planner = pathlib.Path(sys.argv[2]).read_text(encoding="utf-8")
    src_route_test = pathlib.Path(sys.argv[3]).read_text(encoding="utf-8")
    out_dir = pathlib.Path(sys.argv[4])
    out_dir.mkdir(parents=True, exist_ok=True)

    route_test = src_route_test.replace('BASE = "/home/ubuntu/Desktop/job-hunt-nhung"',
                                        f'BASE = "{BASE}"')
    route_test = route_test.replace("Writes /home/ubuntu/Desktop/job-hunt-nhung/route_test.json",
                                    f"Writes {BASE}/route_test.json")
    route_test = reword(route_test)
    assert "nhung" not in route_test.lower(), "an identity string survived the rewrite"
    (out_dir / "route_test.py").write_text(route_test, encoding="utf-8")
    print(f"wrote {out_dir/'route_test.py'} ({len(route_test)} chars)")

    accounts = src_accounts.replace(
        'VAULT = "/home/ubuntu/.hermes/profiles/nhung/vault"', f'VAULT = "{VAULT}"')
    accounts = accounts.replace('EMAIL = "nhung.giap.2912@gmail.com"', f'EMAIL = "{EMAIL}"')
    accounts = accounts.replace('PORTAL_PASSWORD = "Sollicitatie2026!"',
                                f'PORTAL_PASSWORD = "{PORTAL_PASSWORD}"')
    accounts = accounts.replace("$HOME/.hermes/profiles/nhung/vault/ats_accounts.json",
                                "$HOME/.hermes/profiles/vishal/vault/ats_accounts.json")
    accounts = reword(accounts)
    assert "nhung" not in accounts.lower(), "an identity string survived the rewrite"
    assert VAULT in accounts and EMAIL in accounts and PORTAL_PASSWORD in accounts

    planner = src_planner.replace('BASE = Path("/home/ubuntu/Desktop/job-hunt-nhung")',
                                  f'BASE = Path("{BASE}")')
    planner = reword(planner)
    planner = planner.replace(
        "Writes route_plan.json and prints the distribution.",
        "For THIS candidate a manual route is resolved by the HR application email\n"
        "(delivery.failed_apply_route = hr_email), not by a Telegram apply-link hand-off, so\n"
        "manual_browser is the fallback the sweep's email route takes.\n\n"
        "Writes route_plan.json and prints the distribution.")
    assert "nhung" not in planner.lower(), "an identity string survived the rewrite"
    assert BASE in planner

    (out_dir / "accounts.py").write_text(accounts, encoding="utf-8")
    (out_dir / "route_planner.py").write_text(planner, encoding="utf-8")
    print(f"wrote {out_dir/'accounts.py'} ({len(accounts)} chars)")
    print(f"wrote {out_dir/'route_planner.py'} ({len(planner)} chars)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
