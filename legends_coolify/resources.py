"""Offline resource discovery for wheel installs without a source checkout.

Contract (0.2.0): resolve the knowledge root, the entry recipe and the
pack file list from either the installed ``legends_coolify._data`` mirror
(source ``package_data``) or the exact source checkout parent validated by
module marker (source ``checkout``), else ``missing``. Pack content is
authored separately; this module only resolves, lists and verifies it.

Output fields: source, root, recipe, pack_dir, pack_manifest, pack_files,
plus truncated, manifest, verified_files, complete and note. ``complete``
requires a valid pack manifest whose every declared vault file exists
with a matching SHA-256, plus an entry recipe; the CLI exits nonzero
and offline doctor fails unless complete.
"""
import json
import os
import re
from hashlib import sha256
from importlib import resources as importlib_resources
from pathlib import Path, PureWindowsPath

from . import __version__

DATA_PACKAGE = "legends_coolify._data"
KNOWLEDGE_RELATIVE = Path("knowledge")
PACK_MANIFEST_RELATIVE = Path("knowledge") / "coolify" / "pack.json"
VAULT_RELATIVE = Path("knowledge") / "coolify" / "vault"
PACK_SCHEMA = "legends.knowledge-pack/v1"
PACK_MODULE = "legends-coolify"
RECIPE_CANDIDATES = ("docs/AGENT-RECIPE.md", "docs/KNOWLEDGE-PACK.md", "docs/KNOWLEDGE.md")
LIST_LIMIT = 1000
MANIFEST_LIMIT_BYTES = 1024 * 1024
VAULT_FILE_LIMIT_BYTES = 8 * 1024 * 1024
VAULT_FILE_COUNT_LIMIT = 500


def _package_root():
    try:
        base = importlib_resources.files(DATA_PACKAGE)
    except (ModuleNotFoundError, ImportError):
        return None
    try:
        path = Path(os.fspath(base))
    except TypeError:
        return None
    return path if path.is_dir() else None


def _checkout_root():
    """Exact parent of the package directory, validated by module marker."""
    root = Path(__file__).resolve().parent.parent
    marker = root / "pyproject.toml"
    try:
        if not marker.is_file():
            return None
        text = marker.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError):
        return None
    if "legends-coolify" not in text:
        return None
    return root


def _read_manifest(path):
    try:
        raw = path.read_bytes()
    except OSError:
        return None, "pack manifest is unreadable"
    if len(raw) > MANIFEST_LIMIT_BYTES:
        return None, "pack manifest exceeds the size limit"
    try:
        data = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeError):
        return None, "pack manifest is not valid JSON"
    if not isinstance(data, dict):
        return None, "pack manifest must be a JSON object"
    return data, None


def _bounded_parts(value):
    if not isinstance(value, str) or not value or len(value) > 256:
        return None
    if "\\" in value or value.startswith("/") or ":" in value or "\x00" in value:
        return None
    if PureWindowsPath(value).drive:
        return None
    parts = value.split("/")
    if any(part in ("", ".", "..") for part in parts):
        return None
    return parts


def _safe_join(base, parts):
    """Join bounded parts, refusing symlinked components and base escape."""
    node = base
    for part in parts:
        node = node / part
        if node.is_symlink():
            return None
    try:
        anchor = base.resolve()
        resolved = node.resolve()
    except OSError:
        return None
    if not resolved.is_relative_to(anchor):
        return None
    return node


def _sha256_of(path):
    digest = sha256()
    total = 0
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(65536)
            if not chunk:
                break
            total += len(chunk)
            if total > VAULT_FILE_LIMIT_BYTES:
                return None
            digest.update(chunk)
    return digest.hexdigest()


def verify_pack(vault_dir, manifest):
    """Check manifest identity and every declared vault file hash.

    Returns (verified_count, error_note). Only declared files are read;
    nothing else in the tree is scanned.
    """
    if manifest.get("schema") != PACK_SCHEMA:
        return 0, "pack manifest schema mismatch"
    if manifest.get("module") != PACK_MODULE:
        return 0, "pack manifest module mismatch"
    if manifest.get("version") != __version__:
        return 0, "pack manifest version mismatch"
    entry = _bounded_parts(manifest.get("entrypoint"))
    if entry is None:
        return 0, "pack entrypoint is not a bounded relative path"
    entry_target = _safe_join(vault_dir, entry)
    if entry_target is None:
        return 0, "pack entrypoint escapes the vault"
    if not entry_target.is_file():
        return 0, "pack entrypoint is missing"
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        return 0, "pack manifest declares no files"
    if len(files) > VAULT_FILE_COUNT_LIMIT:
        return 0, "pack manifest declares too many files"
    seen = set()
    for item in files:
        if not isinstance(item, dict):
            return 0, "pack manifest file entry is malformed"
        parts = _bounded_parts(item.get("path"))
        digest = item.get("sha256")
        if parts is None or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
            return 0, "pack manifest file entry is malformed"
        key = "/".join(parts)
        if key in seen:
            return 0, "pack manifest declares a duplicate file"
        seen.add(key)
        target = _safe_join(vault_dir, parts)
        if target is None:
            return 0, "pack file path escapes the vault: %s" % key
        if not target.is_file():
            return 0, "pack file is missing: %s" % key
        try:
            actual = _sha256_of(target)
        except OSError:
            return 0, "pack file is unreadable: %s" % key
        if actual is None:
            return 0, "pack file exceeds the size limit: %s" % key
        if actual != digest.lower():
            return 0, "pack file hash mismatch: %s" % key
    if "/".join(entry) not in seen:
        return 0, "pack entrypoint is not a declared file"
    return len(files), None


def _list_files(pack_dir):
    found = []
    truncated = False
    stack = [pack_dir]
    visited = 0
    while stack:
        node = stack.pop()
        visited += 1
        if visited > 5000:
            return sorted(found), True
        try:
            children = sorted(node.iterdir(), key=lambda entry: entry.name)
        except OSError:
            return sorted(found), True
        for child in children:
            name = child.name
            if not name or name.startswith("."):
                continue
            if child.is_symlink():
                continue
            if child.is_dir():
                stack.append(child)
            elif child.is_file():
                found.append(str(child))
                if len(found) >= LIST_LIMIT:
                    return sorted(found), True
    return sorted(found), truncated


def _resolve_recipe(root, manifest):
    candidates = []
    if isinstance(manifest, dict) and isinstance(manifest.get("recipe"), str):
        candidates.append(manifest["recipe"])
    candidates.extend(RECIPE_CANDIDATES)
    for candidate in candidates:
        parts = _bounded_parts(candidate)
        if parts is None:
            continue
        path = _safe_join(root, parts)
        if path is not None and path.is_file():
            return path
    return None


def resolve():
    """Return the resource map with source, root, recipe, pack_dir, pack_manifest and pack_files."""
    root = _package_root()
    source = "package_data"
    if root is None:
        root = _checkout_root()
        source = "checkout"
    if root is None:
        return {"source": "missing", "root": None, "recipe": None, "pack_dir": None,
                "pack_manifest": None, "pack_files": [], "truncated": False,
                "manifest": None, "verified_files": 0, "complete": False, "note": None}
    manifest_path = root / PACK_MANIFEST_RELATIVE
    manifest, note = (None, None)
    pack_manifest = None
    if manifest_path.is_file() and not manifest_path.is_symlink():
        pack_manifest = str(manifest_path)
        manifest, note = _read_manifest(manifest_path)
    pack_dir = root / KNOWLEDGE_RELATIVE
    pack_dir_out = str(pack_dir) if pack_dir.is_dir() else None
    pack_files, truncated = _list_files(pack_dir) if pack_dir_out else ([], False)
    recipe = _resolve_recipe(root, manifest)
    verified = 0
    if pack_manifest is not None and manifest is not None and pack_dir_out:
        verified, verify_note = verify_pack(pack_dir / "coolify" / "vault", manifest)
        if verify_note is not None:
            note = verify_note
    if note is None and pack_manifest is None:
        note = "pack manifest not found"
    if note is None and recipe is None:
        note = "entry recipe not found"
    return {"source": source, "root": str(root), "recipe": str(recipe) if recipe else None,
            "pack_dir": pack_dir_out, "pack_manifest": pack_manifest, "pack_files": pack_files,
            "truncated": truncated, "manifest": manifest, "verified_files": verified,
            "complete": note is None, "note": note}


def status():
    """One-line availability for doctor; never raises."""
    try:
        found = resolve()
    except OSError:
        return {"status": "unreadable", "source": "unknown"}
    if found["complete"]:
        return {"status": "available", "source": found["source"],
                "pack_files": len(found["pack_files"]),
                "verified_files": found["verified_files"]}
    if found["source"] == "missing":
        return {"status": "missing", "source": "missing"}
    return {"status": "incomplete", "source": found["source"]}
