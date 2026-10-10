import argparse
from contextlib import redirect_stderr
import hashlib
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from legends_coolify import __version__, resources
from legends_coolify.cli import main, run
from legends_coolify.client import CoolifyError


PACK = Path("knowledge") / "coolify" / "pack.json"
VAULT = Path("knowledge") / "coolify" / "vault"
ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "legends.knowledge-pack/v1"
MODULE = "legends-coolify"


def write_pack(root, vault_files=None, manifest_patch=None, manifest_override=None, with_recipe=True):
    vault_files = {"index.md": "# index\n", "notes/a.md": "# a\n"} if vault_files is None else vault_files
    entries = []
    for rel, content in vault_files.items():
        data = content.encode("utf-8") if isinstance(content, str) else content
        target = root / VAULT / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        entries.append({"path": rel, "sha256": hashlib.sha256(data).hexdigest()})
    manifest = {"schema": SCHEMA, "id": "coolify", "module": MODULE,
                "version": __version__, "entrypoint": "index.md", "files": entries}
    if manifest_patch:
        manifest.update(manifest_patch)
    pack_path = root / PACK
    pack_path.parent.mkdir(parents=True, exist_ok=True)
    if manifest_override is None:
        payload = json.dumps(manifest)
    elif isinstance(manifest_override, str):
        payload = manifest_override
    else:
        payload = json.dumps(manifest_override)
    pack_path.write_text(payload, encoding="utf-8")
    if with_recipe:
        docs = root / "docs"
        docs.mkdir(parents=True, exist_ok=True)
        (docs / "AGENT-RECIPE.md").write_text("# recipe\n", encoding="utf-8")
        (docs / "KNOWLEDGE-PACK.md").write_text("# pack\n", encoding="utf-8")
    return root


def expected_pack_files(root):
    return sorted(str(root / "knowledge" / "coolify" / name)
                  for name in ("pack.json", "vault/index.md", "vault/notes/a.md"))


class Resolve(unittest.TestCase):
    def test_missing_pack(self):
        with patch.object(resources, "_package_root", return_value=None):
            with patch.object(resources, "_checkout_root", return_value=None):
                found = resources.resolve()
        self.assertEqual(found["source"], "missing")
        self.assertIsNone(found["root"])
        self.assertIsNone(found["pack_dir"])
        self.assertIsNone(found["pack_manifest"])
        self.assertIsNone(found["recipe"])
        self.assertEqual(found["pack_files"], [])
        self.assertEqual(found["verified_files"], 0)
        self.assertFalse(found["complete"])

    def test_package_source_shape(self):
        with tempfile.TemporaryDirectory() as folder:
            root = write_pack(Path(folder) / "data")
            with patch.object(resources, "_package_root", return_value=root):
                with patch.object(resources, "_checkout_root", return_value=None):
                    found = resources.resolve()
        self.assertEqual(found["source"], "package_data")
        self.assertEqual(found["root"], str(root))
        self.assertEqual(found["pack_dir"], str(root / "knowledge"))
        self.assertEqual(found["pack_manifest"], str(root / PACK))
        self.assertEqual(found["pack_files"], expected_pack_files(root))
        self.assertTrue(all(Path(entry).is_absolute() for entry in found["pack_files"]))
        self.assertEqual(found["recipe"], str(root / "docs" / "AGENT-RECIPE.md"))
        self.assertEqual(found["manifest"]["module"], MODULE)
        self.assertFalse(found["truncated"])
        self.assertEqual(found["verified_files"], 2)
        self.assertTrue(found["complete"])
        self.assertIsNone(found["note"])

    def test_checkout_fallback(self):
        with tempfile.TemporaryDirectory() as folder:
            root = write_pack(Path(folder) / "repo")
            with patch.object(resources, "_package_root", return_value=None):
                with patch.object(resources, "_checkout_root", return_value=root):
                    found = resources.resolve()
        self.assertEqual(found["source"], "checkout")
        self.assertEqual(found["pack_dir"], str(root / "knowledge"))
        self.assertTrue(found["complete"])

    def test_checkout_marker_is_exact_parent(self):
        self.assertEqual(resources._checkout_root(), ROOT)

    def test_hidden_symlink_and_dotfiles_skipped(self):
        with tempfile.TemporaryDirectory() as folder:
            root = write_pack(Path(folder) / "data")
            (root / VAULT / ".hidden.md").write_text("# h\n", encoding="utf-8")
            link = root / VAULT / "link.md"
            try:
                link.symlink_to(root / VAULT / "index.md")
            except (OSError, NotImplementedError):
                pass
            with patch.object(resources, "_package_root", return_value=root):
                found = resources.resolve()
        self.assertEqual(found["pack_files"], expected_pack_files(root))
        self.assertTrue(found["complete"])

    def test_recipe_from_manifest(self):
        with tempfile.TemporaryDirectory() as folder:
            root = write_pack(Path(folder) / "data", manifest_patch={"recipe": "docs/custom.md"})
            (root / "docs" / "custom.md").write_text("# custom\n", encoding="utf-8")
            with patch.object(resources, "_package_root", return_value=root):
                found = resources.resolve()
        self.assertEqual(found["recipe"], str(root / "docs" / "custom.md"))
        self.assertTrue(found["complete"])

    def test_recipe_unsafe_manifest_ignored(self):
        for bad in ("../evil.md", "/abs.md", "a\\b.md", "docs/../../evil.md"):
            with tempfile.TemporaryDirectory() as folder:
                root = write_pack(Path(folder) / "data", manifest_patch={"recipe": bad})
                with patch.object(resources, "_package_root", return_value=root):
                    found = resources.resolve()
            self.assertEqual(found["recipe"], str(root / "docs" / "AGENT-RECIPE.md"), bad)

    def test_incomplete_no_manifest(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "data"
            (root / "docs").mkdir(parents=True)
            (root / "docs" / "AGENT-RECIPE.md").write_text("# r\n", encoding="utf-8")
            with patch.object(resources, "_package_root", return_value=root):
                found = resources.resolve()
        self.assertEqual(found["source"], "package_data")
        self.assertIsNone(found["pack_manifest"])
        self.assertIsNone(found["pack_dir"])
        self.assertEqual(found["pack_files"], [])
        self.assertFalse(found["complete"])
        self.assertIn("manifest", found["note"])

    def test_incomplete_no_recipe(self):
        with tempfile.TemporaryDirectory() as folder:
            root = write_pack(Path(folder) / "data", with_recipe=False)
            with patch.object(resources, "_package_root", return_value=root):
                found = resources.resolve()
        self.assertIsNone(found["recipe"])
        self.assertFalse(found["complete"])
        self.assertIn("recipe", found["note"])

    def test_empty_manifest_incomplete(self):
        with tempfile.TemporaryDirectory() as folder:
            root = write_pack(Path(folder) / "data", manifest_override={})
            with patch.object(resources, "_package_root", return_value=root):
                found = resources.resolve()
        self.assertFalse(found["complete"])
        self.assertIn("schema", found["note"])

    def test_manifest_invalid(self):
        for manifest in ("not json", "[1, 2]"):
            with tempfile.TemporaryDirectory() as folder:
                root = write_pack(Path(folder) / "data", manifest_override=manifest)
                with patch.object(resources, "_package_root", return_value=root):
                    found = resources.resolve()
            self.assertIsNone(found["manifest"])
            self.assertFalse(found["complete"])
            self.assertTrue(found["note"])

    def test_manifest_size_cap(self):
        with tempfile.TemporaryDirectory() as folder:
            root = write_pack(Path(folder) / "data",
                              manifest_override="{" + " " * (resources.MANIFEST_LIMIT_BYTES + 1) + "}")
            with patch.object(resources, "_package_root", return_value=root):
                found = resources.resolve()
        self.assertFalse(found["complete"])
        self.assertIn("size limit", found["note"])

    def test_verify_missing_file(self):
        with tempfile.TemporaryDirectory() as folder:
            root = write_pack(Path(folder) / "data")
            (root / VAULT / "notes" / "a.md").unlink()
            with patch.object(resources, "_package_root", return_value=root):
                found = resources.resolve()
        self.assertFalse(found["complete"])
        self.assertIn("notes/a.md", found["note"])

    def test_verify_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as folder:
            root = write_pack(Path(folder) / "data")
            (root / VAULT / "index.md").write_text("# tampered\n", encoding="utf-8")
            with patch.object(resources, "_package_root", return_value=root):
                found = resources.resolve()
        self.assertFalse(found["complete"])
        self.assertIn("hash mismatch", found["note"])

    def test_verify_identity(self):
        cases = ({"schema": "other/v9"}, {"module": "other"}, {"version": "9.9.9"})
        for patch_map in cases:
            with tempfile.TemporaryDirectory() as folder:
                root = write_pack(Path(folder) / "data", manifest_patch=patch_map)
                with patch.object(resources, "_package_root", return_value=root):
                    found = resources.resolve()
            self.assertFalse(found["complete"], patch_map)
            self.assertIn("mismatch", found["note"])

    def test_verify_entrypoint(self):
        for entrypoint in ("../evil.md", "/abs.md", "gone.md"):
            with tempfile.TemporaryDirectory() as folder:
                root = write_pack(Path(folder) / "data", manifest_patch={"entrypoint": entrypoint})
                with patch.object(resources, "_package_root", return_value=root):
                    found = resources.resolve()
            self.assertFalse(found["complete"], entrypoint)
            self.assertIn("entrypoint", found["note"])

    def test_verify_entrypoint_must_be_declared(self):
        with tempfile.TemporaryDirectory() as folder:
            root = write_pack(Path(folder) / "data", manifest_patch={
                "files": [{"path": "notes/a.md",
                           "sha256": hashlib.sha256(b"# a\n").hexdigest()}]})
            with patch.object(resources, "_package_root", return_value=root):
                found = resources.resolve()
        self.assertFalse(found["complete"])
        self.assertIn("not a declared file", found["note"])

    def test_verify_traversal_and_duplicates(self):
        digest = "0" * 64
        bad_lists = ([{"path": "../evil.md", "sha256": digest}],
                     [{"path": "a.md", "sha256": digest}, {"path": "a.md", "sha256": digest}],
                     [{"path": "a.md", "sha256": "zzz"}],
                     [],
                     "not-a-list")
        for files in bad_lists:
            with tempfile.TemporaryDirectory() as folder:
                root = write_pack(Path(folder) / "data", manifest_patch={"files": files})
                with patch.object(resources, "_package_root", return_value=root):
                    found = resources.resolve()
            self.assertFalse(found["complete"], files)

    def test_verify_drive_stream_and_nul_rejected(self):
        for bad in ("C:/evil.md", "C:evil.md", "vault/a.md:stream", "a\x00.md",
                    "//server/share.md", "sub//a.md"):
            files = [{"path": bad, "sha256": "0" * 64}]
            with tempfile.TemporaryDirectory() as folder:
                root = write_pack(Path(folder) / "data", manifest_patch={"files": files})
                with patch.object(resources, "_package_root", return_value=root):
                    found = resources.resolve()
            self.assertFalse(found["complete"], bad)

    def test_verify_symlinked_subdir_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            folder_path = Path(folder)
            outside = folder_path / "outside"
            outside.mkdir()
            planted = outside / "evil.md"
            planted.write_bytes(b"planted")
            digest = hashlib.sha256(b"planted").hexdigest()
            root = write_pack(folder_path / "data", manifest_patch={
                "files": [{"path": "sub/evil.md", "sha256": digest}]})
            link = root / VAULT / "sub"
            try:
                link.symlink_to(outside, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable")
            with patch.object(resources, "_package_root", return_value=root):
                found = resources.resolve()
        self.assertFalse(found["complete"])
        self.assertIn("escapes the vault", found["note"])

    def test_recipe_symlinked_dir_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            folder_path = Path(folder)
            outside = folder_path / "outside"
            outside.mkdir()
            (outside / "AGENT-RECIPE.md").write_text("# planted\n", encoding="utf-8")
            root = write_pack(folder_path / "data", with_recipe=False)
            try:
                (root / "docs").symlink_to(outside, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable")
            with patch.object(resources, "_package_root", return_value=root):
                found = resources.resolve()
        self.assertIsNone(found["recipe"])
        self.assertFalse(found["complete"])

    def test_list_truncation(self):
        with tempfile.TemporaryDirectory() as folder:
            root = write_pack(Path(folder) / "data")
            with patch.object(resources, "_package_root", return_value=root):
                with patch.object(resources, "LIST_LIMIT", 2):
                    found = resources.resolve()
        self.assertTrue(found["truncated"])
        self.assertEqual(len(found["pack_files"]), 2)

    def test_status_never_raises(self):
        with patch.object(resources, "resolve", side_effect=OSError("disk")):
            self.assertEqual(resources.status()["status"], "unreadable")
        with patch.object(resources, "resolve", return_value={"source": "missing", "complete": False}):
            self.assertEqual(resources.status()["status"], "missing")
        with patch.object(resources, "resolve",
                          return_value={"source": "checkout", "complete": False}):
            self.assertEqual(resources.status()["status"], "incomplete")


class Command(unittest.TestCase):
    def test_resources_reports_frozen_shape(self):
        with tempfile.TemporaryDirectory() as folder:
            root = write_pack(Path(folder) / "data")
            with patch.object(resources, "_package_root", return_value=root):
                report = run(argparse.Namespace(command="resources"))
        self.assertEqual(report["status"], "pass")
        for key in ("source", "root", "recipe", "pack_dir", "pack_manifest", "pack_files"):
            self.assertIn(key, report)
        self.assertEqual(report["source"], "package_data")

    def test_resources_missing_errors(self):
        with patch.object(resources, "_package_root", return_value=None):
            with patch.object(resources, "_checkout_root", return_value=None):
                with self.assertRaises(CoolifyError):
                    run(argparse.Namespace(command="resources"))
                with redirect_stderr(StringIO()):
                    self.assertEqual(main(["resources"]), 1)

    def test_resources_incomplete_errors(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "data"
            (root / "docs").mkdir(parents=True)
            (root / "docs" / "AGENT-RECIPE.md").write_text("# r\n", encoding="utf-8")
            with patch.object(resources, "_package_root", return_value=root):
                with self.assertRaises(CoolifyError):
                    run(argparse.Namespace(command="resources"))
                with redirect_stderr(StringIO()) as err:
                    self.assertEqual(main(["resources"]), 1)
                self.assertIn("incomplete", err.getvalue())

    def test_doctor_offline_incomplete_errors(self):
        incomplete = {"status": "incomplete", "source": "checkout"}
        with patch("legends_coolify.cli.resources_status", return_value=incomplete):
            with self.assertRaises(CoolifyError):
                run(argparse.Namespace(command="doctor", live=False))
            with redirect_stderr(StringIO()) as err:
                self.assertEqual(main(["doctor"]), 1)
            self.assertIn("incomplete", err.getvalue())

    def test_doctor_offline_available_passes(self):
        available = {"status": "available", "source": "package_data",
                     "pack_files": 4, "verified_files": 2}
        with patch("legends_coolify.cli.resources_status", return_value=available):
            report = run(argparse.Namespace(command="doctor", live=False))
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["resources"], available)


if __name__ == "__main__":
    unittest.main()
