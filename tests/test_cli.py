import argparse
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from legends_coolify.client import Client, CoolifyError, NoRedirect, allowed_path, records, status_summary
from legends_coolify.cli import main, run, write_report


class Fake:
    def __init__(self, replies):
        self.replies = replies
        self.calls = []
        self.params = []

    def get(self, path, params=None):
        self.calls.append(path)
        self.params.append(params or {})
        reply = self.replies[path]
        if isinstance(reply, Exception):
            raise reply
        return reply


def args(command, **kwargs):
    defaults = {"command": command, "live": False, "uuid": "demo-app",
                "deployment_uuid": None, "limit": 10, "skip": 0, "out": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


AVAILABLE = {"status": "available", "source": "package_data", "pack_files": 1}


class Boundaries(unittest.TestCase):
    def test_only_reviewed_paths(self):
        for path in ("/applications", "/applications/demo-app", "/applications/demo-app/envs", "/databases/demo-db/backups", "/health",
                     "/deployments", "/deployments/cm37r6cqj000008jm0veg5tkm", "/deployments/applications/demo-app"):
            self.assertTrue(allowed_path(path), path)
        for path in ("/deploy", "/applications/x/start", "/databases/x/restart", "/services/x/stop", "/applications/../deploy", "/applications/%2e%2e", "https://example.org/applications", "//example.org", "/applications?token=secret", "/applications/x/envs/", "/applications/x/backups", "/databases/x/envs", "/applications/x\n",
                     "/deployments/applications", "/applications/x/logs", "/databases/x/logs", "/services/x/logs", "/deployments/x/cancel",
                     "/databases/x/backups/y/executions", "/deployments/applications/x?take=5", "/deployments/applications/x/"):
            self.assertFalse(allowed_path(path), repr(path))

    def test_invalid_origin(self):
        for origin in ("", "http://example.org", "https://user:pass@example.org", "https://example.org/api/v1", "https://example.org/?secret=x", "https://example.org/#x", "https://example.org:0", "https://example.org:bad", "https://exa mple.org"):
            with self.assertRaises(CoolifyError):
                Client(origin, "test-token")

    def test_invalid_token(self):
        for token in ("", "has space", "tab\there", "nul\x00here", "non-ascii-t\xc3\xb6k\xc3\xa9n", "ctrl\x1fchar", "del\x7fchar"):
            with self.assertRaises(CoolifyError):
                Client("https://example.org", token)
        Client("https://example.org", "67|abcXYZ0123-._~")

    def test_block_before_network(self):
        client = Client("https://example.org", "test-token")
        with patch.object(client._opener, "open") as network:
            with self.assertRaises(CoolifyError):
                client.get("/applications/x/start")
            network.assert_not_called()

    def test_transport_value_error_maps(self):
        client = Client("https://example.org", "test-token")
        with patch.object(client._opener, "open", side_effect=ValueError("Invalid header value")):
            with self.assertRaises(CoolifyError):
                client.get("/applications")

    def test_redirect_refused(self):
        self.assertIsNone(NoRedirect().redirect_request(None, None, 302, "redirect", {}, "https://other.example"))

    def test_error_body_not_exposed(self):
        client = Client("https://example.org", "test-token")
        body = StringIO("secret-body")
        error = HTTPError("https://example.org", 403, "secret-message", {}, body)
        with patch.object(client._opener, "open", side_effect=error):
            with self.assertRaisesRegex(CoolifyError, "HTTP 403") as caught:
                client.get("/applications")
            self.assertNotIn("secret", str(caught.exception))
        self.assertTrue(body.closed)

    def test_get_only_and_bounded_response(self):
        client = Client("https://example.org", "test-token")
        with patch.object(client._opener, "open") as network:
            network.return_value.__enter__.return_value.read.return_value = b'[]'
            self.assertEqual(client.get("/applications"), [])
            request = network.call_args.args[0]
            self.assertEqual(request.method, "GET")
            self.assertEqual(request.full_url, "https://example.org/api/v1/applications")
            self.assertIsNone(request.data)

    def test_secret_values_never_exported(self):
        fake = Fake({"/applications/demo-app/envs": [{"key": "NEXT_PUBLIC_APP_URL", "value": "secret-sentinel", "real_value": "secret-sentinel", "is_runtime": True}]})
        report = run(args("env"), fake)
        self.assertNotIn("secret-sentinel", json.dumps(report))
        self.assertEqual(report["variables"][0]["key"], "NEXT_PUBLIC_APP_URL")
        self.assertFalse(report["values_included"])

    def test_inventory_whitelist(self):
        fake = Fake({"/" + kind: [{"uuid": "x", "name": "demo", "status": "running:unhealthy", "password": "secret-sentinel", "private_key": "secret-sentinel", "ip": "secret-sentinel", "fqdn": "secret-sentinel"}]
                     for kind in ("applications", "databases", "services", "servers", "projects")})
        report = run(args("inventory"), fake)
        self.assertNotIn("secret-sentinel", json.dumps(report))
        self.assertEqual(report["status"], "pass")

    def test_partial_inventory_is_explicit(self):
        fake = Fake({"/applications": [], "/databases": [], "/services": CoolifyError("HTTP 403")})
        report = run(args("health"), fake)
        self.assertEqual(report["status"], "partial")
        self.assertNotIn("services", report["resources"])
        self.assertIn("services", report["errors"])

    def test_unexpected_shape_is_not_empty_success(self):
        for value in (None, "error", {}, {"message": "unauthorized"}, ["bad"]):
            with self.assertRaises(CoolifyError):
                records(value)
        for value in ({"data": [], "meta": {"current_page": 1, "last_page": 2}},
                      {"data": [], "links": {"next": "https://example.org/?page=2"}},
                      {"data": [], "total": 5}):
            with self.assertRaisesRegex(CoolifyError, "Paginated"):
                records(value)
        self.assertEqual(records({"data": []}), [])

    def test_status_is_not_substring_health(self):
        self.assertFalse(status_summary("exited:unhealthy")["running"])
        self.assertTrue(status_summary("exited:unhealthy")["stopped"])
        self.assertEqual(status_summary("running:unhealthy")["health"], "unhealthy")
        self.assertTrue(status_summary("running:unhealthy")["running"])
        self.assertEqual(status_summary(None)["health"], "unknown")

    def test_backup_claims_are_limited(self):
        fake = Fake({"/databases/demo-app/backups": [{"uuid": "backup", "enabled": True, "frequency": "daily", "s3_password": "secret-sentinel"}]})
        report = run(args("backups"), fake)
        self.assertFalse(report["restore_verified"])
        self.assertFalse(report["execution_success_verified"])
        self.assertNotIn("secret-sentinel", json.dumps(report))

    def test_plan_does_not_mutate(self):
        fake = Fake({"/applications/demo-app": {"uuid": "demo-app", "name": "demo", "password": "secret-sentinel"}})
        report = run(args("plan"), fake)
        self.assertEqual(fake.calls, ["/applications/demo-app"])
        self.assertFalse(report["executed"])
        self.assertNotIn("secret-sentinel", json.dumps(report))

    def test_incomplete_rows_fail(self):
        for command, path in (("env", "/applications/demo-app/envs"), ("backups", "/databases/demo-app/backups")):
            with self.assertRaises(CoolifyError):
                run(args(command), Fake({path: [{}]}))
        fake = Fake({"/applications": [{}], "/databases": [], "/services": []})
        report = run(args("health"), fake)
        self.assertEqual(report["status"], "partial")
        self.assertIn("applications", report["errors"])

    def test_plan_target_must_match(self):
        for reply in ({}, {"message": "not found"}, {"uuid": "different"}):
            with self.assertRaises(CoolifyError):
                run(args("plan"), Fake({"/applications/demo-app": reply}))

    def test_live_doctor_requires_authenticated_request(self):
        fake = Fake({"/health": "OK", "/applications": CoolifyError("HTTP 401"), "/version": "v4.0.0"})
        options = args("doctor")
        options.live = True
        with self.assertRaises(CoolifyError):
            run(options, fake)
        self.assertEqual(fake.calls, ["/health", "/applications"])

    def test_live_doctor_requires_uuid_rows(self):
        fake = Fake({"/health": "OK", "/applications": [{}], "/version": "v4.0.0"})
        options = args("doctor")
        options.live = True
        with self.assertRaises(CoolifyError):
            run(options, fake)

    def test_live_doctor_reports_version(self):
        fake = Fake({"/health": "OK", "/applications": [{"uuid": "a", "name": "n", "status": "running:healthy"}], "/version": "v4.0.0"})
        options = args("doctor")
        options.live = True
        report = run(options, fake)
        self.assertEqual(report["application_count"], 1)
        self.assertEqual(report["instance_version"], "v4.0.0")
        self.assertEqual(fake.calls, ["/health", "/applications", "/version"])

    def test_live_doctor_tolerates_missing_version(self):
        fake = Fake({"/health": "OK", "/applications": [{"uuid": "a", "name": "n"}], "/version": CoolifyError("HTTP 404")})
        options = args("doctor")
        options.live = True
        report = run(options, fake)
        self.assertEqual(report["status"], "pass")
        self.assertIsNone(report["instance_version"])

    def test_offline_doctor_never_opens_network(self):
        with patch("legends_coolify.cli.Client", side_effect=AssertionError("network")):
            with patch("legends_coolify.cli.resources_status", return_value=AVAILABLE):
                self.assertFalse(run(args("doctor"))["live_access_verified"])

    def test_cli_scrubs_reflected_token(self):
        output = StringIO()
        with patch.dict(os.environ, {"COOLIFY_API_TOKEN": "secret-sentinel"}), patch("legends_coolify.cli.run", return_value={"status": "pass", "name": "secret-sentinel"}), redirect_stdout(output):
            self.assertEqual(main(["inventory"]), 0)
        self.assertNotIn("secret-sentinel", output.getvalue())

    def test_output_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "report.json"
            path.write_text("preserve", encoding="utf-8")
            with redirect_stderr(StringIO()):
                self.assertEqual(main(["doctor", "--out", str(path)]), 1)
            self.assertEqual(path.read_text(), "preserve")

    def test_output_requires_parent(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "nodir" / "report.json"
            with redirect_stderr(StringIO()) as err:
                self.assertEqual(main(["doctor", "--out", str(path)]), 1)
            self.assertIn("parent directory", err.getvalue())

    def test_output_refuses_symlink(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "target.json"
            target.write_text("preserve", encoding="utf-8")
            link = Path(folder) / "report.json"
            try:
                os.symlink(target, link)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable")
            with redirect_stderr(StringIO()) as err:
                self.assertEqual(main(["doctor", "--out", str(link)]), 1)
            self.assertIn("symlink", err.getvalue())
            self.assertEqual(target.read_text(), "preserve")

    def test_output_restricts_permissions(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "report.json"
            with patch("legends_coolify.cli.resources_status", return_value=AVAILABLE):
                with redirect_stderr(StringIO()):
                    self.assertEqual(main(["doctor", "--out", str(path)]), 0)
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "pass")
            if os.name == "posix":
                self.assertEqual(stat.S_IMODE(os.stat(path).st_mode) & 0o077, 0)

    def test_write_failure_removes_created_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "report.json"
            with patch("legends_coolify.cli.os.fdopen", side_effect=OSError("disk full")):
                with self.assertRaises(OSError):
                    write_report(path, "{}")
            self.assertFalse(path.exists())

    def test_write_failure_preserves_replacement(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "report.json"
            other = Path(folder) / "other.json"
            other.write_text("replacement", encoding="utf-8")

            def clobber(fd, *pos, **key):
                os.close(fd)
                os.replace(other, path)
                raise OSError("disk full")

            with patch("legends_coolify.cli.os.fdopen", side_effect=clobber):
                with self.assertRaises(OSError):
                    write_report(path, "{}")
            self.assertEqual(path.read_text(encoding="utf-8"), "replacement")


if __name__ == "__main__":
    unittest.main()
