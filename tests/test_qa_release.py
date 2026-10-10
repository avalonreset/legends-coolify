"""Independent QA boundaries: transport edges, malformed shapes, output safety.

Probes failure modes the primary suite does not pin, plus regression cover
for the release-checker enhancements. Fixtures that must trip the residue
scanner are assembled at runtime so this file itself stays clean.
"""
import argparse
from contextlib import redirect_stderr
from io import StringIO
import importlib.util
import json
import os
import struct
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from legends_coolify.cli import main, run
from legends_coolify.client import (
    Client, CoolifyError, allowed_path, records, status_summary,
)

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "qa_check_release", ROOT / "scripts" / "check_release.py")
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


def args(command, **kwargs):
    params = {"command": command, "live": False, "uuid": "demo-app", "out": None}
    params.update(kwargs)
    return argparse.Namespace(**params)


def sk_live_fixture():
    return "sk_" + "live_" + "a" * 12


def tailnet_fixture():
    # Synthetic tailnet-style hostname; never a real fingerprint.
    return "node.tail" + "abc123" + ".ts.net"


class TransportEdges(unittest.TestCase):
    def test_token_with_whitespace_rejected(self):
        for token in ("a b", "a\nb", "a\tb", "a\rb", ""):
            with self.assertRaises(CoolifyError, msg=repr(token)):
                Client("https://example.org", token)

    def test_valid_origins_accepted(self):
        for origin in ("https://example.org", "https://example.org/",
                       "https://example.org:8443", "https://coolify.example.com"):
            client = Client(origin, "test-token")
            self.assertEqual(client.timeout, 20)
            self.assertFalse(client.base_url.endswith("/"))

    def test_oversize_body_rejected(self):
        client = Client("https://example.org", "test-token")
        with patch.object(client._opener, "open") as network:
            network.return_value.__enter__.return_value.read.return_value = (
                b"x" * (8 * 1024 * 1024 + 1))
            with self.assertRaisesRegex(CoolifyError, "8 MiB"):
                client.get("/applications")

    def test_non_utf8_body_rejected_without_leak(self):
        client = Client("https://example.org", "test-token")
        with patch.object(client._opener, "open") as network:
            network.return_value.__enter__.return_value.read.return_value = (
                b"\xff\xfe\x00secret-bytes")
            with self.assertRaises(CoolifyError) as caught:
                client.get("/applications")
            self.assertNotIn("secret", str(caught.exception))

    def test_http_error_code_reported_body_omitted(self):
        client = Client("https://example.org", "test-token")
        for code in (401, 403, 404, 500):
            error = HTTPError("https://example.org", code, "reason",
                              {}, StringIO("body-secret"))
            with patch.object(client._opener, "open", side_effect=error):
                with self.assertRaises(CoolifyError) as caught:
                    client.get("/servers")
                self.assertIn(str(code), str(caught.exception))
                self.assertNotIn("secret", str(caught.exception))


class ShapeEdges(unittest.TestCase):
    def test_data_envelope_must_hold_list(self):
        for value in ({"data": {"uuid": "x"}}, {"data": None},
                      {"data": "x"}, {"data": (1, 2)}):
            with self.assertRaises(CoolifyError, msg=repr(value)):
                records(value)

    def test_blank_identifiers_rejected(self):
        from legends_coolify.client import backup_summary, env_summary, summary
        for func, row in ((summary, {"uuid": ""}),
                          (summary, {"uuid": None}),
                          (env_summary, {"key": ""}),
                          (backup_summary, {"uuid": ""})):
            with self.assertRaises(CoolifyError, msg=repr(row)):
                func(row)

    def test_non_string_status_is_unknown_not_crash(self):
        for value in (123, ["running"], {"status": "running"}, True):
            result = status_summary(value)
            self.assertEqual(result["health"], "unknown")
            self.assertFalse(result["running"])
            self.assertFalse(result["stopped"])

    def test_path_case_and_slash_variants_rejected(self):
        for path in ("/health/", "/version/", "/APPLICATIONS",
                     "/Applications", "/SERVERS", "/Health"):
            self.assertFalse(allowed_path(path), repr(path))

    def test_live_doctor_accepts_ok_shapes_only(self):
        from legends_coolify.client import records as _records

        class Fake:
            def __init__(self, health):
                self.health = health

            def get(self, path):
                if path == "/health":
                    return self.health
                return []

        for health in ("OK", "ok", "  OK  ", {"status": "ok"}, {"status": "OK"}):
            options = args("doctor", live=True)
            report = run(options, Fake(health))
            self.assertTrue(report["live_access_verified"], repr(health))
        for health in ("FAIL", "", {}, {"status": "bad"}, {"other": 1}, None, []):
            with self.assertRaises(CoolifyError, msg=repr(health)):
                run(args("doctor", live=True), Fake(health))
        self.assertEqual(_records([]), [])


class OutputSafety(unittest.TestCase):
    def test_missing_parent_dir_is_generic_error(self):
        output = StringIO()
        missing = Path("qa-missing-dir-7f3a") / "report.json"
        self.assertFalse(missing.parent.exists())
        with patch.dict(os.environ, {"COOLIFY_API_TOKEN": "secret-sentinel"}):
            with redirect_stderr(output):
                code = main(["doctor", "--out", str(missing)])
        self.assertEqual(code, 1)
        self.assertNotIn("secret-sentinel", output.getvalue())
        self.assertNotIn("qa-missing-dir", output.getvalue())

    def test_error_message_with_reflected_token_is_scrubbed(self):
        output = StringIO()
        with patch.dict(os.environ, {"COOLIFY_API_TOKEN": "secret-sentinel"}):
            with patch("legends_coolify.cli.run",
                       side_effect=CoolifyError("denied for secret-sentinel")):
                with redirect_stderr(output):
                    code = main(["inventory"])
        self.assertEqual(code, 1)
        self.assertNotIn("secret-sentinel", output.getvalue())


def minimal_tree(root):
    for name in CHECK.REQUIRED:
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# fixture\n", encoding="utf-8")


class CheckerEnhancements(unittest.TestCase):
    def test_clean_tree_passes(self):
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            minimal_tree(root)
            self.assertEqual(CHECK.check(root), [])

    def test_root_flag_scopes_check(self):
        import subprocess
        import sys
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            minimal_tree(root)
            proc = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "check_release.py"),
                 "--root", str(root)],
                capture_output=True, text=True, timeout=60)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("PASS", proc.stdout)

    def test_key_material_files_rejected(self):
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            minimal_tree(root)
            (root / "deploy.key").write_text("key", encoding="utf-8")
            (root / "notes.txt").write_text("plain\n", encoding="utf-8")
            errors = CHECK.check(root)
            self.assertTrue(any("deploy.key" in e for e in errors), errors)
            nested = root / ".integration" / "empire"
            nested.mkdir(parents=True)
            (nested / "pinned.pem").write_text("key", encoding="utf-8")
            self.assertEqual(CHECK.check(root), errors)

    def test_text_suffix_residue_scanned(self):
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            minimal_tree(root)
            (root / "notes.txt").write_text(
                "token " + sk_live_fixture() + "\n", encoding="utf-8")
            (root / "box.tailnet").write_text(tailnet_fixture() + "\n",
                                              encoding="utf-8")
            errors = CHECK.check(root)
            self.assertTrue(any("notes.txt" in e for e in errors), errors)
            # Unknown suffixes stay out of the text scan.
            self.assertFalse(any("box.tailnet" in e for e in errors), errors)

    def test_manifest_mismatch_rejected(self):
        import hashlib
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            minimal_tree(root)
            assets = root / "assets"
            assets.mkdir()
            (assets / "a.bin").write_bytes(b"raw-bytes")
            good = {"files": [{"name": "a.bin", "bytes": 9,
                               "sha256": hashlib.sha256(b"raw-bytes").hexdigest()}]}
            (assets / "manifest.json").write_text(json.dumps(good), encoding="utf-8")
            self.assertEqual(CHECK.check(root), [])
            bad = {"files": [{"name": "a.bin", "bytes": 9, "sha256": "0" * 64}]}
            (assets / "manifest.json").write_text(json.dumps(bad), encoding="utf-8")
            errors = CHECK.check(root)
            self.assertTrue(any("hash mismatch" in e for e in errors), errors)

    def test_png_text_chunk_rejected(self):
        import tempfile
        import zlib

        def chunk(kind, payload):
            return (struct.pack(">I", len(payload)) + kind + payload
                    + struct.pack(">I", zlib.crc32(kind + payload)))

        clean = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", b"\x00" * 13)
                 + chunk(b"IDAT", b"\x00") + chunk(b"IEND", b""))
        dirty = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", b"\x00" * 13)
                 + chunk(b"tEXt", b"Author\x00someone") + chunk(b"IDAT", b"\x00")
                 + chunk(b"IEND", b""))
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            minimal_tree(root)
            (root / "clean.png").write_bytes(clean)
            (root / "dirty.png").write_bytes(dirty)
            self.assertEqual(CHECK.image_metadata_issues(root / "clean.png"), [])
            direct = CHECK.image_metadata_issues(root / "dirty.png")
            self.assertTrue(any("tEXt" in e for e in direct), direct)
            (root / "dirty.png").unlink()
            self.assertEqual(CHECK.check(root), [])
            (root / "dirty.png").write_bytes(dirty)
            errors = CHECK.check(root)
            self.assertTrue(any("tEXt" in e for e in errors), errors)

    def test_webp_exif_rejected(self):
        import tempfile
        clean = b"RIFF\x0c\x00\x00\x00WEBPVP8L\x04\x00\x00\x00\x00\x00\x00\x00"
        exif_payload = b"II*\x00" + b"\x00" * 8
        exif = (b"RIFF" + struct.pack("<I", 4 + 8 + len(exif_payload) + 8 + 4)
                + b"WEBPVP8L\x04\x00\x00\x00\x00\x00\x00\x00"
                + b"EXIF" + struct.pack("<I", len(exif_payload)) + exif_payload)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            minimal_tree(root)
            (root / "clean.webp").write_bytes(clean)
            self.assertEqual(CHECK.check(root), [])
            (root / "dirty.webp").write_bytes(exif)
            errors = CHECK.check(root)
            self.assertTrue(any("EXIF" in e for e in errors), errors)


if __name__ == "__main__":
    unittest.main()
