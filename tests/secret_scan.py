"""Scan the files git is about to commit for anything that must never be pushed.

    python tests/secret_scan.py      (run from the repo root; exit 1 if anything is found)

Private strings to look for (webhook host, mailbox names) go one per line in
secrets/scan-patterns.txt, which is never committed.
"""
import re
import subprocess
import sys
from pathlib import Path

PATTERNS = {
    "email address": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z0-9.-]+"),
    "GitHub token": re.compile(r"\b(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}"),
    "API key": re.compile(r"\b(sk-[A-Za-z0-9-]{20,}|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{30,}|xox[abp]-[A-Za-z0-9-]{10,})"),
    "secret assignment": re.compile(r"(?i)\b(token|secret|password|api[_-]?key)\s*[:=]\s*['\"][^'\"<>{}]{12,}['\"]"),
    "private key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
}
private = Path("secrets/scan-patterns.txt")
if not private.exists():
    sys.exit("secret scan: secrets/scan-patterns.txt is missing")
for line in private.read_text(encoding="utf-8").splitlines():
    if line.strip():
        PATTERNS[f"private pattern {line.strip()[:4]}…"] = re.compile(re.escape(line.strip()), re.I)

files = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
                       capture_output=True, text=True, check=True).stdout.split()
hits = []
for path in files:
    try:
        text = open(path, encoding="utf-8").read()
    except (UnicodeDecodeError, FileNotFoundError):
        continue
    for n, line in enumerate(text.splitlines(), start=1):
        for name, pat in PATTERNS.items():
            if pat.search(line):
                hits.append(f"{path}:{n}: {name}: {line.strip()[:120]}")
print(f"scanned {len(files)} staged files")
print("\n".join(hits) if hits else "nothing found")
sys.exit(1 if hits else 0)
