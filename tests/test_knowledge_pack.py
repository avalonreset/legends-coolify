"""Offline checks for the Empire knowledge pack manifest and shelf links."""
import hashlib
import json
import re
from pathlib import Path
import unittest
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "knowledge" / "coolify" / "pack.json"
VAULT = PACK.parent / "vault"


def load_manifest():
    return json.loads(PACK.read_bytes().decode("utf-8"))


class PackContract(unittest.TestCase):
    def test_manifest_identity(self):
        manifest = load_manifest()
        self.assertEqual(manifest["schema"], "legends.knowledge-pack/v1")
        self.assertEqual(manifest["id"], "coolify")
        self.assertEqual(manifest["module"], "legends-coolify")
        self.assertRegex(manifest["version"], r"^\d+\.\d+\.\d+$")
        self.assertEqual(manifest["entrypoint"], "index.md")
        ontology = manifest["ontology"]
        self.assertEqual(ontology["kind"], "library")
        self.assertTrue(ontology["suggested_home"].startswith("wiki/library/"))
        self.assertTrue(ontology["purpose"])

    def test_files_match_bytes(self):
        manifest = load_manifest()
        files = manifest["files"]
        self.assertLessEqual(len(files), 256)
        total = 0
        seen = set()
        for item in files:
            rel = item["path"]
            self.assertRegex(item["sha256"], r"^[0-9a-f]{64}$")
            self.assertFalse(Path(rel).is_absolute(), rel)
            self.assertNotIn("..", Path(rel).parts, rel)
            self.assertTrue(rel.endswith(".md"), rel)
            lowered = rel.lower()
            self.assertNotIn(lowered, seen, f"case alias: {rel}")
            seen.add(lowered)
            data = (VAULT / rel).read_bytes()
            data.decode("utf-8")
            self.assertEqual(hashlib.sha256(data).hexdigest(), item["sha256"], rel)
            total += len(data)
        self.assertLessEqual(total, 8 * 1024 * 1024)
        declared = {item["path"] for item in files}
        self.assertIn(manifest["entrypoint"], declared)
        on_disk = {p.relative_to(VAULT).as_posix()
                   for p in VAULT.rglob("*") if p.is_file()}
        self.assertEqual(declared, on_disk)

    def test_shelf_links_resolve_inside_shelf(self):
        manifest = load_manifest()
        declared = {item["path"] for item in manifest["files"]}
        checked = 0
        for rel in sorted(declared):
            text = (VAULT / rel).read_text(encoding="utf-8")
            for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
                if target.startswith(("https://", "http://", "mailto:", "#")):
                    continue
                target = unquote(target.split("#", 1)[0].split("?", 1)[0])
                resolved = ((VAULT / rel).parent / target).resolve()
                self.assertTrue(
                    resolved.is_relative_to(VAULT.resolve()),
                    f"{rel}: {target} escapes the shelf")
                self.assertTrue(resolved.is_file(), f"{rel}: {target}")
                checked += 1
        self.assertGreater(checked, 0)

    def test_index_lists_every_top_level_page(self):
        manifest = load_manifest()
        index = (VAULT / "index.md").read_text(encoding="utf-8")
        for item in manifest["files"]:
            rel = item["path"]
            if "/" in rel:
                continue
            self.assertIn(f"`{rel}`", index, rel)


if __name__ == "__main__":
    unittest.main()
