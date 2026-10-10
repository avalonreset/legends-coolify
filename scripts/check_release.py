"""Offline release checks for links, private residue and required artifacts."""
import argparse
from pathlib import Path
import re
import struct
import sys
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
SKIP = {".git", ".venv", "dist", "build", "__pycache__", ".integration"}
REQUIRED = ["README.md", "LICENSE", "AGENTS.md", "SECURITY.md", "wiki/index.md",
            "references/sources.md", "docs/AGENT-RECIPE.md", "docs/RELEASE.md",
            "templates/private-operation-receipt.md", "skills/cto-legends/SKILL.md"]
TEXT_SUFFIXES = {".md", ".py", ".json", ".toml", ".yml", ".in", ".txt", ".cfg", ".ini"}
# Private infrastructure patterns are encoded to avoid including the actual
# house identifiers in the released checker itself.
FORBIDDEN = [r"(?i)[a-z]:\\users\\", r"(?i)\.tail[a-z0-9]+\.ts\.net",
             r"(?i)sk_live_[a-z0-9]{12,}", r"gh[pousr]_[A-Za-z0-9]{20,}",
             r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----"]
FORBIDDEN_FILES = {".pem", ".key", ".p12", ".pfx"}
PNG_METADATA_CHUNKS = {"tEXt", "iTXt", "zTXt", "eXIf"}
WEBP_METADATA_CHUNKS = {b"EXIF", b"XMP "}


def image_metadata_issues(path):
    """Flag raster metadata chunks that can carry authoring residue."""
    try:
        raw = path.read_bytes()
    except OSError:
        return ["Cannot read image: %s" % path]
    issues = []
    suffix = path.suffix.lower()
    if suffix == ".png":
        if raw[:8] != b"\x89PNG\r\n\x1a\n":
            return ["Not a PNG file: %s" % path]
        offset = 8
        while offset + 8 <= len(raw):
            length = struct.unpack(">I", raw[offset:offset + 4])[0]
            chunk = raw[offset + 4:offset + 8]
            try:
                name = chunk.decode("latin1")
            except UnicodeError:
                break
            if name in PNG_METADATA_CHUNKS:
                issues.append(f"Image metadata chunk {name} in {path.name}; strip authoring residue.")
            if name == "IEND":
                break
            offset += 12 + length
    elif suffix == ".webp":
        if raw[:4] != b"RIFF" or raw[8:12] != b"WEBP":
            return ["Not a WebP file: %s" % path]
        offset = 12
        while offset + 8 <= len(raw):
            tag = raw[offset:offset + 4]
            length = struct.unpack("<I", raw[offset + 4:offset + 8])[0]
            if tag in WEBP_METADATA_CHUNKS:
                issues.append(f"Image metadata chunk {tag!r} in {path.name}; strip authoring residue.")
                break
            offset += 8 + length + (length % 2)
    return issues


def check(root=ROOT):
    errors = []
    for name in REQUIRED:
        if not (root / name).is_file():
            errors.append(f"Missing required file: {name}")
    manifest = root / "assets" / "manifest.json"
    if manifest.is_file():
        import hashlib
        import json
        try:
            entries = json.loads(manifest.read_text(encoding="utf-8-sig"))["files"]
        except (ValueError, KeyError):
            errors.append("assets/manifest.json is not a manifest with files.")
            entries = []
        for entry in entries:
            target = root / "assets" / entry.get("name", "")
            try:
                raw = target.read_bytes()
            except OSError:
                errors.append(f"Manifest asset missing: {entry.get('name')}")
                continue
            if len(raw) != entry.get("bytes"):
                errors.append(f"Manifest byte mismatch: {entry.get('name')}")
            if hashlib.sha256(raw).hexdigest() != entry.get("sha256"):
                errors.append(f"Manifest hash mismatch: {entry.get('name')}")
    for path in root.rglob("*"):
        rel = path.relative_to(root)
        if not path.is_file() or any(p in SKIP or p.endswith(".egg-info") for p in rel.parts):
            continue
        if path.suffix.lower() in FORBIDDEN_FILES:
            errors.append(f"Private key material must not ship: {rel}")
            continue
        if path.suffix.lower() in {".png", ".webp"}:
            errors.extend(f"{rel}: {issue}" for issue in image_metadata_issues(path))
            continue
        if path.suffix not in TEXT_SUFFIXES:
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
    parser = argparse.ArgumentParser(description="Offline release checks.")
    parser.add_argument("--root", type=Path, default=ROOT)
    options = parser.parse_args()
    failures = check(options.root)
    for failure in failures:
        print(failure)
    print(f"Release checks: {'FAIL' if failures else 'PASS'} ({len(failures)} issues)")
    sys.exit(bool(failures))
