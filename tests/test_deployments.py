import argparse
from contextlib import redirect_stderr
from io import StringIO
import json
import unittest
from unittest.mock import patch

from legends_coolify import __version__
from legends_coolify.cli import main, run
from legends_coolify.client import Client, CoolifyError, deployment_summary, deployment_window


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


def args(**kwargs):
    defaults = {"command": "deployments", "live": False, "uuid": None,
                "deployment_uuid": None, "limit": 10, "skip": 0, "out": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def entry(uuid="d1", **over):
    row = {"deployment_uuid": uuid, "status": "finished", "commit": "abc123",
           "commit_message": "ship it", "created_at": "2026-10-01T00:00:00Z",
           "updated_at": "2026-10-01T00:05:00Z"}
    row.update(over)
    return row


class Deployments(unittest.TestCase):
    def test_running_list_is_whitelisted(self):
        item = entry("d1", status="in_progress", logs="secret-sentinel", password="secret-sentinel")
        report = run(args(), Fake({"/deployments": [item]}))
        self.assertEqual(report["scope"], "running")
        self.assertEqual(report["deployments"][0]["outcome"], "active")
        self.assertNotIn("secret-sentinel", json.dumps(report))
        self.assertNotIn("logs", report["deployments"][0])

    def test_outcome_mapping(self):
        cases = {"queued": "active", "in_progress": "active", "finished": "finished",
                 "failed": "failed", "cancelled-by-user": "cancelled",
                 "weird-future-status": "unknown", None: "unknown"}
        for status, outcome in cases.items():
            with self.subTest(status=status):
                self.assertEqual(deployment_summary(entry(status=status))["outcome"], outcome)

    def test_missing_uuid_fails(self):
        with self.assertRaises(CoolifyError):
            run(args(), Fake({"/deployments": [{}]}))
        with self.assertRaises(CoolifyError):
            run(args(deployment_uuid="d1"), Fake({"/deployments/d1": {}}))

    def test_single_deployment_matches_target(self):
        report = run(args(deployment_uuid="d1"), Fake({"/deployments/d1": entry("d1")}))
        self.assertEqual(report["deployment"]["deployment_uuid"], "d1")

    def test_single_deployment_mismatch_fails(self):
        with self.assertRaisesRegex(CoolifyError, "does not match"):
            run(args(deployment_uuid="d1"), Fake({"/deployments/d1": entry("other")}))

    def test_single_deployment_non_dict_fails(self):
        with self.assertRaises(CoolifyError):
            run(args(deployment_uuid="d1"), Fake({"/deployments/d1": [entry("d1")]}))

    def test_history_window_report(self):
        rows = [entry("d%d" % n) for n in range(10)]
        fake = Fake({"/deployments/applications/demo-app": {"count": 25, "deployments": rows}})
        report = run(args(uuid="demo-app"), fake)
        self.assertEqual(report["total_count"], 25)
        self.assertEqual(report["returned_count"], 10)
        self.assertEqual((report["skip"], report["take"]), (0, 10))
        self.assertTrue(report["has_more"])
        self.assertEqual(fake.calls, ["/deployments/applications/demo-app"])
        self.assertEqual(fake.params, [{"skip": 0, "take": 10}])

    def test_history_final_page(self):
        rows = [entry("d%d" % n) for n in range(5)]
        fake = Fake({"/deployments/applications/demo-app": {"count": 25, "deployments": rows}})
        report = run(args(uuid="demo-app", skip=20, limit=10), fake)
        self.assertFalse(report["has_more"])
        self.assertEqual(report["returned_count"], 5)
        self.assertEqual(fake.params, [{"skip": 20, "take": 10}])

    def test_history_empty(self):
        fake = Fake({"/deployments/applications/demo-app": {"count": 0, "deployments": []}})
        report = run(args(uuid="demo-app"), fake)
        self.assertEqual(report["total_count"], 0)
        self.assertFalse(report["has_more"])

    def test_history_inconsistent_total_fails(self):
        fake = Fake({"/deployments/applications/demo-app": {"count": 0, "deployments": [entry()]}})
        with self.assertRaisesRegex(CoolifyError, "Inconsistent"):
            run(args(uuid="demo-app"), fake)

    def test_history_over_limit_fails(self):
        rows = [entry("d%d" % n) for n in range(3)]
        fake = Fake({"/deployments/applications/demo-app": {"count": 10, "deployments": rows}})
        with self.assertRaisesRegex(CoolifyError, "Inconsistent"):
            run(args(uuid="demo-app", limit=2), fake)

    def test_history_over_total_fails(self):
        rows = [entry("d%d" % n) for n in range(10)]
        fake = Fake({"/deployments/applications/demo-app": {"count": 25, "deployments": rows}})
        with self.assertRaisesRegex(CoolifyError, "Inconsistent"):
            run(args(uuid="demo-app", skip=20, limit=10), fake)

    def test_history_past_end_empty_permitted(self):
        for skip, total in ((30, 25), (25, 25)):
            fake = Fake({"/deployments/applications/demo-app": {"count": total, "deployments": []}})
            report = run(args(uuid="demo-app", skip=skip, limit=10), fake)
            self.assertFalse(report["has_more"])
            self.assertEqual(report["returned_count"], 0)

    def test_history_past_end_nonempty_fails(self):
        fake = Fake({"/deployments/applications/demo-app": {"count": 25, "deployments": [entry()]}})
        with self.assertRaisesRegex(CoolifyError, "Inconsistent"):
            run(args(uuid="demo-app", skip=25, limit=10), fake)

    def test_history_empty_below_total_fails(self):
        fake = Fake({"/deployments/applications/demo-app": {"count": 25, "deployments": []}})
        with self.assertRaisesRegex(CoolifyError, "Inconsistent"):
            run(args(uuid="demo-app", skip=0, limit=10), fake)

    def test_history_missing_count_fails(self):
        for value in ({"deployments": []}, {"count": True, "deployments": []},
                      {"count": -1, "deployments": []}, {"count": "25", "deployments": []}):
            with self.assertRaisesRegex(CoolifyError, "total count is missing"):
                deployment_window(value, 0, 10)

    def test_history_bare_list_fails(self):
        with self.assertRaisesRegex(CoolifyError, "partial window"):
            deployment_window([entry()], 0, 10)

    def test_history_bad_window_args(self):
        value = {"count": 0, "deployments": []}
        for skip, take in ((-1, 10), (0, 0), (True, 10), (0, False), ("0", 10)):
            with self.assertRaises(CoolifyError):
                deployment_window(value, skip, take)

    def test_query_url_exact(self):
        client = Client("https://example.org", "test-token")
        with patch.object(client._opener, "open") as network:
            network.return_value.__enter__.return_value.read.return_value = b'{"count":0,"deployments":[]}'
            self.assertEqual(client.get("/deployments/applications/demo-app", {"take": 7, "skip": 5}),
                             {"count": 0, "deployments": []})
            request = network.call_args.args[0]
            self.assertEqual(request.method, "GET")
            self.assertEqual(request.full_url,
                             "https://example.org/api/v1/deployments/applications/demo-app?skip=5&take=7")
            self.assertEqual(request.get_header("User-agent"), "legends-coolify/" + __version__)

    def test_query_rejected_before_network(self):
        client = Client("https://example.org", "test-token")
        bad = [("skip", -1), ("take", 0), ("take", 51), ("take", True),
               ("skip", "5"), ("unknown", 1)]
        for key, value in bad:
            with patch.object(client._opener, "open") as network:
                with self.assertRaises(CoolifyError):
                    client.get("/deployments/applications/demo-app", {key: value})
                network.assert_not_called()
        with patch.object(client._opener, "open") as network:
            with self.assertRaises(CoolifyError):
                client.get("/applications", {"take": 5})
            network.assert_not_called()

    def test_cli_targets_exclusive(self):
        with redirect_stderr(StringIO()):
            with self.assertRaises(SystemExit) as caught:
                main(["deployments", "--uuid", "a", "--deployment-uuid", "b"])
        self.assertEqual(caught.exception.code, 2)

    def test_cli_window_bounds(self):
        for argv in (["deployments", "--uuid", "a", "--limit", "0"],
                    ["deployments", "--uuid", "a", "--limit", "51"],
                    ["deployments", "--uuid", "a", "--skip", "-1"]):
            with redirect_stderr(StringIO()):
                with self.assertRaises(SystemExit) as caught:
                    main(argv)
            self.assertEqual(caught.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
