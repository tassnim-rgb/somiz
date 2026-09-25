"""Rudimentary secrets scanner for tracked files.

Scans every git-tracked file (``git ls-files -z``) for high-signal secret
patterns and exits 1 if anything matches, so CI fails before a key is ever
pushed (see .github/workflows/ci.yml). Local run::

    python scripts/scan_secrets.py

Exit codes: 0 = clean, 1 = matches found, 2 = git unavailable.

Commented-out lines (the placeholders in ``.env.example``, for instance) are
skipped only for the *generic* assignment pattern; high-signal patterns such
as Vercel or GitHub tokens are checked on every line, comments included.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import List, Pattern, Tuple

PATTERNS: List[Tuple[str, Pattern[str], bool]] = [
    ("vercel-token", re.compile(r"\bvcp_[A-Za-z0-9]{24,}\b"), False),
    ("github-pat", re.compile(r"\bghp_[A-Za-z0-9]{30,}\b"), False),
    ("github-app", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{40,}\b"), False),
    ("openai-key", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"), False),
    ("aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b"), False),
    ("slack-token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"), False),
    ("private-key",
     re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
     False),
    # generic key/token/password/secret assignments: skip commented-out lines
    # because .env.example documents placeholder values that way
    ("generic-assignment",
     re.compile(r"""(?i)(?:api[_-]?key|secret|token|password|passwd)\s*[:=]\s*["'][^"']{16,}["']"""),
     True),
]


def tracked_files() -> List[Path]:
    """Paths of every file git tracks in the repository."""
    try:
        out = subprocess.run(
            ["git", "ls-files", "-z", "--recurse-submodules"],
            capture_output=True, text=False, check=False,
        )
    except FileNotFoundError:
        raise RuntimeError("git is not on PATH")
    if out.returncode != 0:
        raise RuntimeError("cannot enumerate tracked files (git unavailable)")
    root = Path(__file__).resolve().parents[1]
    return [root / p.decode("utf-8") for p in out.stdout.split(b"\0") if p]


def scan_file(path: Path) -> List[str]:
    """Human-readable findings for one file, or []."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    findings: List[str] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for name, pattern, skip_comments in PATTERNS:
            if skip_comments and line.lstrip().startswith("#"):
                continue
            for match in pattern.finditer(line):
                found = match.group(0)
                snippet = found if len(found) <= 24 \
                    else found[:10] + "..." + found[-10:]
                findings.append(
                    f"{path.relative_to(Path.cwd())}:{lineno} [{name}] {snippet}")
    return findings


def main() -> int:
    try:
        files = tracked_files()
    except RuntimeError as exc:
        print(f"scan_secrets: {exc}", file=sys.stderr)
        return 2
    hits: List[str] = []
    for path in files:
        hits.extend(scan_file(path))
    if hits:
        print(f"scan_secrets: {len(hits)} potential secret(s) in tracked files:")
        for hit in hits:
            print("  " + hit)
        return 1
    print(f"scan_secrets: OK ({len(files)} tracked files, no secret patterns)")
    return 0


if __name__ == "__main__":
    sys.exit(main())