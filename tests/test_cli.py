import argparse
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from legends_coolify.client import Client, CoolifyError, NoRedirect, allowed_path, records, status_summary
from legends_coolify.cli import main, run


class Fake:
    def __init__(self, replies):
        self.replies = replies
        self.calls = []

    def get(self, path):
        self.calls.append(path)
        reply = self.replies[path]
        if isinstance(reply, Exception):
            raise reply
        return reply


def args(command, **kwargs):
    return argparse.Namespace(command=command, live=False, uuid="demo-app", out=None, **kwargs)


class Boundaries(unittest.TestCase):
    def test_only_reviewed_paths(self):
        for path in ("/applications", "/applications/demo-app", "/applications/demo-app/envs", "/databases/demo-db/backups", "/health"):
            self.assertTrue(allowed_path(path), path)
        for path in ("/deploy", "/applications/x/start", "/databases/x/restart", "/services/x/stop", "/applications/../deploy", "/applications/%2e%2e", "https://example.org/applications", "//example.org", "/applications?token=secret", "/applications/x/envs/", "/applications/x/backups", "/databases/x/envs", "/applications/x\n"):
            self.assertFalse(allowed_path(path), repr(path))

    def test_invalid_origin(self):
        for origin in ("", "http://example.org", "https://user:pass@example.org", "https://example.org/api/v1", "https://example.org/?secret=x", "https://example.org/#x", "https://example.org:0", "https://example.org:bad", "https://exa mple.org"):
            with self.assertRaises(CoolifyError):
                Client(origin, "test-token")

    def test_block_before_network(self):
        client = Client("https://example.org", "test-token")
        with patch.object(client._opener, "open") as network:
            with self.assertRaises(CoolifyError):
                client.get("/applications/x/start")
            network.assert_not_called()

    def test_redirect_refused(self):
        self.assertIsNone(NoRedirect().redirect_request(None, None, 302, "redirect", {}, "https://other.example"))

    def test_error_body_not_exposed(self):
        client = Client("https://example.org", "test-token")
        error = HTTPError("https://example.org", 403, "secret-message", {}, StringIO("secret-body"))
        with patch.object(client._opener, "open", side_effect=error):
            with self.assertRaisesRegex(CoolifyError, "HTTP 403") as caught:
                client.get("/applications")
            self.assertNotIn("secret", str(caught.exception))

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
        fake = Fake({"/health": "OK", "/applications": CoolifyError("HTTP 401")})
        options = args("doctor")
        options.live = True
        with self.assertRaises(CoolifyError):
            run(options, fake)
        self.assertEqual(fake.calls, ["/health", "/applications"])

    def test_offline_doctor_never_opens_network(self):
        with patch("legends_coolify.cli.Client", side_effect=AssertionError("network")):
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


if __name__ == "__main__":
    unittest.main()
