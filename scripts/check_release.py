"""Offline release checks for links, private residue and required artifacts."""
from pathlib import Path
import re
import sys
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
SKIP = {".git", ".venv", "dist", "build", "__pycache__"}
REQUIRED = ["README.md", "LICENSE", "AGENTS.md", "SECURITY.md", "wiki/index.md",
            "references/sources.md", "docs/AGENT-RECIPE.md", "docs/RELEASE.md",
            "templates/private-operation-receipt.md", "skills/cto-legends/SKILL.md"]
# Private infrastructure patterns are encoded to avoid including the actual
# house identifiers in the released checker itself.
FORBIDDEN = [r"(?i)[a-z]:\\users\\", r"(?i)\.tail[a-z0-9]+\.ts\.net",
             r"(?i)sk_live_[a-z0-9]{12,}", r"gh[pousr]_[A-Za-z0-9]{20,}",
             r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----"]


def check(root=ROOT):
    errors = []
    for name in REQUIRED:
        if not (root / name).is_file():
            errors.append(f"Missing required file: {name}")
    for path in root.rglob("*"):
        rel = path.relative_to(root)
        if not path.is_file() or any(p in SKIP or p.endswith(".egg-info") for p in rel.parts):
            continue
        if path.suffix not in {".md", ".py", ".json", ".toml", ".yml", ".in"}:
            continue
        text = path.read_text(encoding="utf-8-sig")
        if path.name != "check_release.py":
            for pattern in FORBIDDEN:
                if re.search(pattern, text):
                    errors.append(f"Possible private residue: {rel}")
        if path.suffix != ".md":
            continue
        if "\u2014" in text or "\u2013" in text:
            errors.append(f"Disallowed dash in copy: {rel}")
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
            if target.startswith(("https://", "http://", "mailto:", "#")):
                continue
            target = unquote(target.split("#", 1)[0].split("?", 1)[0])
            resolved = (path.parent / target).resolve()
            if not resolved.is_relative_to(root.resolve()) or not resolved.exists():
                errors.append(f"Broken or external local link: {rel}: {target}")
    return errors


if __name__ == "__main__":
    failures = check()
    for failure in failures:
        print(failure)
    print(f"Release checks: {'FAIL' if failures else 'PASS'} ({len(failures)} issues)")
    sys.exit(bool(failures))
