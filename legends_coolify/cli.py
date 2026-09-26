import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

from . import __version__
from .client import Client, CoolifyError, LISTS, backup_summary, env_summary, identifier, records, scrub_token, summary


def run(args, client=None):
    report = {"module": "legends-coolify", "version": __version__, "read_only": True,
              "generated_at": datetime.now(timezone.utc).isoformat(), "command": args.command}
    if args.command == "doctor" and not args.live:
        return {**report, "status": "pass", "mode": "offline", "python": sys.version.split()[0],
                "live_access_verified": False, "next": "Set COOLIFY_BASE_URL and COOLIFY_API_TOKEN; run doctor --live."}
    if client is None:
        client = Client(os.environ.get("COOLIFY_BASE_URL", ""), os.environ.get("COOLIFY_API_TOKEN", ""))
    if args.command == "doctor":
        health = client.get("/health")
        healthy = isinstance(health, str) and health.strip().upper() == "OK"
        if isinstance(health, dict):
            healthy = health.get("status") in ("ok", "OK")
        if not healthy:
            raise CoolifyError("Instance health response did not confirm OK.")
        # Authenticated endpoint: /health alone is not API access proof.
        apps = records(client.get("/applications"))
        return {**report, "status": "pass", "mode": "live", "live_access_verified": True,
                "instance_health": "ok", "application_count": len(apps),
                "application_health_verified": False}
    if args.command in ("inventory", "health"):
        kinds = sorted(LISTS) if args.command == "inventory" else ["applications", "databases", "services"]
        errors = {}
        resources = {}
        for kind in kinds:
            try:
                resources[kind] = [summary(row) for row in records(client.get("/" + kind))]
            except CoolifyError as error:
                errors[kind] = str(error)
        return {**report, "status": "partial" if errors else "pass", "resources": resources,
                "errors": errors, "note": "Status is collection status. Container state does not prove application or database health."}
    uuid = identifier(args.uuid)
    if args.command == "env":
        rows = records(client.get(f"/applications/{uuid}/envs"))
        return {**report, "status": "pass", "uuid": uuid, "values_included": False,
                "variables": [env_summary(row) for row in rows]}
    if args.command == "backups":
        rows = records(client.get(f"/databases/{uuid}/backups"))
        return {**report, "status": "pass", "uuid": uuid,
                "schedules": [backup_summary(row) for row in rows],
                "restore_verified": False, "execution_success_verified": False,
                "note": "Configuration is not proof of a completed backup or a successful restore."}
    if args.command == "plan":
        app = client.get(f"/applications/{uuid}")
        if not isinstance(app, dict) or app.get("uuid") != uuid:
            raise CoolifyError("Application response UUID does not match the requested target.")
        return {**report, "status": "pass", "application": summary(app), "executed": False,
                "checklist": [
                    "Record the exact target, current immutable image or commit, and intended change in your private workspace.",
                    "Verify a restorable database backup and separate persistent-volume recovery; record evidence and recovery time.",
                    "Review schema compatibility: an image rollback does not reverse a database migration.",
                    "Verify environment names, DNS, TLS and application-specific health criteria.",
                    "For a migration, designate one writer and prevent overlapping jobs, webhooks and schedulers.",
                    "Obtain authorization for the exact change; use Coolify's official API, CLI or UI for execution.",
                    "Validate application behavior and dependencies; execute the rehearsed rollback if acceptance fails.",
                ]}
    raise CoolifyError("Unsupported command.")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only Coolify checks. Knowledge vault: wiki/index.md in the source distribution.")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("doctor", "inventory", "health", "env", "backups", "plan"):
        cmd = sub.add_parser(command)
        cmd.add_argument("--out", type=Path, help="Create a new private JSON report; refuses to overwrite existing files.")
        if command == "doctor":
            cmd.add_argument("--live", action="store_true", help="Verify instance health and authenticated application listing.")
        if command in ("env", "backups", "plan"):
            cmd.add_argument("--uuid", required=True)
    args = parser.parse_args(argv)
    try:
        if args.out and args.out.exists():
            raise CoolifyError("Output already exists; choose a new private report path.")
        result = scrub_token(run(args), os.environ.get("COOLIFY_API_TOKEN", ""))
        text = json.dumps(result, indent=2, ensure_ascii=True) + "\n"
        if args.out:
            with args.out.open("x", encoding="utf-8") as handle:
                handle.write(text)
        else:
            sys.stdout.write(text)
        return 1 if result["status"] == "partial" else 0
    except (CoolifyError, OSError) as error:
        # Never include OSError paths, provider bodies, headers or tokens.
        message = str(error) if isinstance(error, CoolifyError) else "Cannot write report; check the private destination directory and permissions."
        print(json.dumps({"status": "error", "error": scrub_token(message, os.environ.get("COOLIFY_API_TOKEN", ""))}), file=sys.stderr)
        return 1
