import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import stat
import sys

from . import __version__
from .client import Client, CoolifyError, LISTS, backup_summary, deployment_summary, deployment_window, env_summary, identifier, records, scrub_token, summary
from .resources import resolve as resolve_resources, status as resources_status

_MACOS_SYSTEM_SYMLINKS = {Path("/var"), Path("/tmp"), Path("/etc")}
_CFA_PROTECTED_NAMES = {
    "desktop",
    "documents",
    "pictures",
    "videos",
    "music",
    "onedrive",
    "favorites",
}


def bounded_int(name, low, high):
    def convert(text):
        try:
            value = int(text)
        except (TypeError, ValueError):
            raise argparse.ArgumentTypeError("%s must be an integer." % name)
        if not low <= value <= high:
            raise argparse.ArgumentTypeError("%s must be between %d and %d." % (name, low, high))
        return value
    return convert


def _is_link_or_reparse(path: Path) -> bool:
    if os.path.islink(path) or path.is_symlink():
        return True
    isjunction = getattr(os.path, "isjunction", None)
    if callable(isjunction) and isjunction(path):
        return True
    try:
        st = os.lstat(path)
    except OSError:
        return False
    return bool(getattr(st, "st_reparse_tag", 0))


def check_no_symlink_chain(path):
    """Refuse leaf or ancestor symlinks/junctions (exempting macOS /var, /tmp, /etc)."""
    current = Path(path)
    while True:
        if _is_link_or_reparse(current):
            if not (sys.platform == "darwin" and current in _MACOS_SYSTEM_SYMLINKS):
                raise CoolifyError(
                    "Refusing to write through a symlink; choose a new private report path."
                )
        parent = current.parent
        if parent == current:
            break
        current = parent


def check_not_cfa_protected(path):
    """Refuse writes into Windows Controlled Folder Access protected directories."""
    target = Path(path)
    try:
        resolved = target.resolve(strict=False)
    except OSError:
        resolved = target.absolute()
    homes = set()
    try:
        homes.add(Path.home().resolve(strict=False))
    except OSError:
        pass
    for env_key in ("USERPROFILE", "HOME"):
        val = os.environ.get(env_key, "").strip()
        if val:
            try:
                homes.add(Path(val).resolve(strict=False))
            except OSError:
                homes.add(Path(val))
    for home in homes:
        for folder_name in _CFA_PROTECTED_NAMES:
            protected = home / folder_name
            try:
                if resolved == protected or resolved.is_relative_to(protected):
                    raise CoolifyError(
                        "Refusing to write into a Windows Controlled Folder Access "
                        "protected directory; choose a workspace report path."
                    )
            except ValueError:
                continue
    if os.name == "nt":
        sys_drive = os.environ.get("SystemDrive", "C:").rstrip("\\/")
        for sys_dir in ("Windows", "Program Files", "Program Files (x86)"):
            protected_sys = Path(sys_drive + "\\" + sys_dir)
            try:
                if resolved == protected_sys or resolved.is_relative_to(protected_sys):
                    raise CoolifyError(
                        "Refusing to write into a Windows Controlled Folder Access "
                        "protected directory; choose a workspace report path."
                    )
            except ValueError:
                continue


def run(args, client=None):
    report = {"module": "legends-coolify", "version": __version__, "read_only": True,
              "generated_at": datetime.now(timezone.utc).isoformat(), "command": args.command}
    if args.command == "doctor" and not args.live:
        availability = resources_status()
        if availability["status"] != "available":
            raise CoolifyError("Required package resources are missing or incomplete; reinstall from the release archive.")
        return {**report, "status": "pass", "mode": "offline", "python": sys.version.split()[0],
                "live_access_verified": False, "resources": availability,
                "next": "Set COOLIFY_BASE_URL and COOLIFY_API_TOKEN; run doctor --live."}
    if args.command == "resources":
        found = resolve_resources()
        if not found.get("complete"):
            raise CoolifyError("Required package resources are missing or incomplete; reinstall from the release archive.")
        return {**report, "status": "pass", **found}
    if client is None:
        allow_private = bool(getattr(args, "allow_private_host", False)) or (
            os.environ.get("COOLIFY_ALLOW_PRIVATE_HOST", "").strip().lower()
            in {"1", "true", "yes"}
        )
        client = Client(
            os.environ.get("COOLIFY_BASE_URL", ""),
            os.environ.get("COOLIFY_API_TOKEN", ""),
            allow_private_host=allow_private,
        )
    if args.command == "doctor":
        health = client.get("/health")
        healthy = isinstance(health, str) and health.strip().upper() == "OK"
        if isinstance(health, dict):
            healthy = health.get("status") in ("ok", "OK")
        if not healthy:
            raise CoolifyError("Instance health response did not confirm OK.")
        # Authenticated endpoint: /health alone is not API access proof.
        # Rows must carry UUIDs; a malformed list is failed readiness, not one app.
        apps = [summary(row) for row in records(client.get("/applications"))]
        try:
            version = client.get("/version")
            instance_version = version.strip() if isinstance(version, str) else None
        except CoolifyError:
            instance_version = None
        return {**report, "status": "pass", "mode": "live", "live_access_verified": True,
                "instance_health": "ok", "application_count": len(apps),
                "instance_version": instance_version, "resources": resources_status(),
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
    if args.command == "deployments":
        if getattr(args, "deployment_uuid", None):
            target = identifier(args.deployment_uuid)
            item = client.get("/deployments/" + target)
            if not isinstance(item, dict):
                raise CoolifyError("Unexpected deployment response.")
            found = deployment_summary(item)
            if found["deployment_uuid"] != target:
                raise CoolifyError("Deployment response UUID does not match the requested target.")
            return {**report, "status": "pass", "deployment": found}
        if getattr(args, "uuid", None):
            uuid = identifier(args.uuid)
            total, items = deployment_window(client.get(
                "/deployments/applications/" + uuid, {"skip": args.skip, "take": args.limit}),
                args.skip, args.limit)
            shown = [deployment_summary(entry) for entry in items]
            return {**report, "status": "pass", "uuid": uuid, "total_count": total,
                    "returned_count": len(shown), "skip": args.skip, "take": args.limit,
                    "has_more": args.skip + len(shown) < total, "deployments": shown,
                    "note": "History window only; total_count covers all retained deployments."}
        rows = records(client.get("/deployments"))
        return {**report, "status": "pass", "scope": "running",
                "deployments": [deployment_summary(row) for row in rows],
                "note": "Currently queued or in-progress deployments; finished history needs --uuid."}
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


def preflight_out(path):
    """Validate the report destination before any network access.

    Fails fast on collisions, missing parents, symlinks/junctions, and CFA
    directories without creating residue; the exclusive create still happens late.
    """
    path = Path(path)
    check_no_symlink_chain(path)
    check_not_cfa_protected(path)
    if path.exists():
        raise CoolifyError("Output already exists; choose a new private report path.")
    if not path.parent.is_dir():
        raise CoolifyError("Report parent directory does not exist; create the private directory first.")


def _created_identity(path, created):
    """True only when path still names the file this process created."""
    try:
        current = os.lstat(path)
    except OSError:
        return False
    return (not stat.S_ISLNK(current.st_mode)
            and current.st_ino == created.st_ino and current.st_dev == created.st_dev)


def _remove_created(path, created):
    if created is not None and _created_identity(path, created):
        try:
            os.unlink(path)
        except OSError:
            pass


def write_report(path, text):
    """Exclusively create a new private report; never overwrite or follow links.

    O_EXCL makes creation atomic; the body streams after. On failure only
    the exact file this call created is removed, never a replacement path.
    """
    path = Path(path)
    check_no_symlink_chain(path)
    check_not_cfa_protected(path)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags, 0o600)
    except FileExistsError:
        raise CoolifyError("Output already exists; choose a new private report path.") from None
    created = None
    try:
        created = os.fstat(fd)
        check_no_symlink_chain(path)
        if not stat.S_ISREG(created.st_mode):
            raise CoolifyError("Refusing to write a report to a non-regular file.")
    except BaseException:
        os.close(fd)
        _remove_created(path, created)
        raise
    try:
        handle = os.fdopen(fd, "w", encoding="utf-8", newline="\n")
    except BaseException:
        os.close(fd)
        _remove_created(path, created)
        raise
    try:
        with handle:
            handle.write(text)
    except BaseException:
        _remove_created(path, created)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only Coolify checks. Knowledge vault: wiki/index.md in the source distribution.")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("doctor", "inventory", "health", "env", "backups", "plan", "deployments", "resources"):
        cmd = sub.add_parser(command)
        if command != "resources":
            cmd.add_argument("--out", type=Path, help="Create a new private JSON report; refuses to overwrite existing files.")
            cmd.add_argument("--allow-private-host", action="store_true",
                             help="Allow private RFC1918, ULA, or Tailscale Coolify origins (loopback and link-local remain blocked).")
        if command == "doctor":
            cmd.add_argument("--live", action="store_true", help="Verify instance health and authenticated application listing.")
        if command in ("env", "backups", "plan"):
            cmd.add_argument("--uuid", required=True)
        if command == "deployments":
            targets = cmd.add_mutually_exclusive_group()
            targets.add_argument("--uuid", help="Application UUID for deployment history.")
            targets.add_argument("--deployment-uuid", help="Single deployment UUID.")
            cmd.add_argument("--limit", type=bounded_int("limit", 1, 50), default=10,
                             help="History window size, 1-50 (default 10).")
            cmd.add_argument("--skip", type=bounded_int("skip", 0, 100000), default=0,
                             help="History window offset (default 0).")
    args = parser.parse_args(argv)
    try:
        if getattr(args, "out", None):
            preflight_out(args.out)
        result = scrub_token(run(args), os.environ.get("COOLIFY_API_TOKEN", ""))
        text = json.dumps(result, indent=2, ensure_ascii=True) + "\n"
        if getattr(args, "out", None):
            write_report(args.out, text)
        else:
            sys.stdout.write(text)
        return 1 if result["status"] == "partial" else 0
    except (CoolifyError, OSError) as error:
        # Never include OSError paths, provider bodies, headers or tokens.
        message = str(error) if isinstance(error, CoolifyError) else "Cannot write report; check the private destination directory and permissions."
        print(json.dumps({"status": "error", "error": scrub_token(message, os.environ.get("COOLIFY_API_TOKEN", ""))}), file=sys.stderr)
        return 1
