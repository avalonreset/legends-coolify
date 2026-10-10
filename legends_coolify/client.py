"""Fixed-endpoint GET client. No raw URL, mutation, redirect or secret-output lane."""
import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from . import __version__


class CoolifyError(Exception):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


LISTS = {"applications", "databases", "services", "servers", "projects"}
DETAIL = re.compile(r"^/(applications|databases)/[A-Za-z0-9_-]{1,128}(?:/(envs|backups))?$")
DEPLOY_DETAIL = re.compile(r"^/deployments/(?:applications/)?[A-Za-z0-9_-]{1,128}$")

# Query windows are only meaningful on the paginated deployment-history route.
# Keys outside this table are rejected before any network access.
HISTORY_PARAMS = {"/deployments/applications/": {"skip": (0, 100000), "take": (1, 50)}}

DEPLOYMENT_OUTCOMES = {
    "queued": "active",
    "in_progress": "active",
    "finished": "finished",
    "failed": "failed",
    "cancelled-by-user": "cancelled",
}


def identifier(value):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", value or ""):
        raise CoolifyError("Invalid resource identifier; use the exact UUID from inventory.")
    return value


def allowed_path(path):
    if path in {"/health", "/version", "/deployments"} | {"/" + item for item in LISTS}:
        return True
    match = DETAIL.fullmatch(path)
    if match and (match[2] is None or (match[1], match[2]) in {
            ("applications", "envs"), ("databases", "backups")}):
        return True
    if path == "/deployments/applications":
        return False
    return bool(DEPLOY_DETAIL.fullmatch(path))


def validated_params(path, params):
    """Accept only the documented integer window for deployment history."""
    if not params:
        return {}
    table = None
    for prefix, allowed in HISTORY_PARAMS.items():
        if path.startswith(prefix) and DEPLOY_DETAIL.fullmatch(path):
            table = allowed
            break
    if table is None:
        raise CoolifyError("Query parameters are only supported for application deployment history.")
    clean = {}
    for key, value in params.items():
        bounds = table.get(key)
        if bounds is None:
            raise CoolifyError("Unsupported query parameter: %s." % key)
        if isinstance(value, bool) or not isinstance(value, int):
            raise CoolifyError("Query parameter %s must be an integer." % key)
        if not bounds[0] <= value <= bounds[1]:
            raise CoolifyError("Query parameter %s must be between %d and %d." % (key, bounds[0], bounds[1]))
        clean[key] = value
    return clean


class Client:
    def __init__(self, base_url, token, *, timeout=20):
        try:
            url = urlsplit(base_url)
            valid = (url.scheme == "https" and url.hostname and not url.username
                     and not url.password and url.path in ("", "/")
                     and not url.query and not url.fragment and url.port != 0
                     and not any(c.isspace() for c in base_url))
        except ValueError:
            valid = False
        if not valid:
            raise CoolifyError("COOLIFY_BASE_URL must be an HTTPS instance origin, without credentials, path, query or fragment.")
        if not token or not re.fullmatch(r"[\x21-\x7E]+", token):
            raise CoolifyError("Set COOLIFY_API_TOKEN to a read-permission token.")
        self.base_url = base_url.rstrip("/")
        self._token = token
        self.timeout = timeout
        # Avoid implicit credential routing through ambient proxy settings.
        self._opener = build_opener(ProxyHandler({}), NoRedirect())

    def get(self, path, params=None):
        if not allowed_path(path):
            raise CoolifyError("Endpoint is outside the read-only allowlist.")
        query = validated_params(path, params or {})
        prefix = "/api" if path == "/health" else "/api/v1"
        url = self.base_url + prefix + path
        if query:
            url += "?" + urlencode(sorted(query.items()))
        try:
            req = Request(url, method="GET", headers={
                "Authorization": "Bearer " + self._token, "Accept": "application/json",
                "User-Agent": "legends-coolify/" + __version__,
            })
            with self._opener.open(req, timeout=self.timeout) as response:
                raw = response.read(8 * 1024 * 1024 + 1)
                if len(raw) > 8 * 1024 * 1024:
                    raise CoolifyError("Response exceeded the 8 MiB limit.")
                text = raw.decode("utf-8")
                if path in {"/health", "/version"}:
                    try:
                        return json.loads(text)
                    except ValueError:
                        return text.strip()
                return json.loads(text)
        except HTTPError as error:
            error.close()
            hint = {
                401: "check that the token is valid and API access is enabled",
                403: "check token permissions, role and team scope",
                404: "check the identifier and instance version support",
                429: "rate limited; wait for Retry-After, then retry with fewer requests",
            }.get(error.code, "check API access, team scope and permissions")
            raise CoolifyError("Coolify returned HTTP %d; %s. Response body omitted." % (error.code, hint)) from None
        except (URLError, OSError, ValueError, UnicodeError):
            raise CoolifyError("Coolify request failed: verify network, TLS, instance URL and response format. Details omitted.") from None


def records(value):
    if isinstance(value, dict):
        if set(value) != {"data"}:
            if "data" in value:
                raise CoolifyError("Paginated list response; refusing to report one page as a complete inventory.")
            raise CoolifyError("Unexpected list response; refusing to report an empty inventory as success.")
        value = value["data"]
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise CoolifyError("Unexpected list response; refusing to report an empty inventory as success.")
    return value


def safe_text(value):
    return value if isinstance(value, str) else None


def status_summary(value):
    raw = safe_text(value)
    parts = (raw or "").lower().split(":")
    return {"status": raw, "running": parts[0] in {"running", "started"},
            "stopped": parts[0] in {"exited", "stopped", "offline"},
            "health": parts[1] if len(parts) > 1 and parts[1] in {"healthy", "unhealthy"} else "unknown"}


def summary(item):
    if not isinstance(item, dict) or not isinstance(item.get("uuid"), str) or not item["uuid"]:
        raise CoolifyError("Unexpected resource response.")
    return {"uuid": safe_text(item.get("uuid")), "name": safe_text(item.get("name")),
            **status_summary(item.get("status"))}


def env_summary(item):
    # Never emit values, even for keys claiming to be public.
    if not isinstance(item.get("key"), str) or not item["key"]:
        raise CoolifyError("Unexpected environment response; variable key is missing.")
    return {"key": safe_text(item.get("key")),
            **{k: item.get(k) if isinstance(item.get(k), bool) else None
               for k in ("is_preview", "is_runtime", "is_buildtime")}}


def backup_summary(item):
    if not isinstance(item.get("uuid"), str) or not item["uuid"]:
        raise CoolifyError("Unexpected backup response; schedule UUID is missing.")
    return {"uuid": safe_text(item.get("uuid")),
            "enabled": item.get("enabled") if isinstance(item.get("enabled"), bool) else None,
            "frequency": safe_text(item.get("frequency")),
            "save_s3": item.get("save_s3") if isinstance(item.get("save_s3"), bool) else None}


def deployment_summary(item):
    # Whitelist only; logs and any future secret-bearing fields never pass.
    if not isinstance(item, dict) or not isinstance(item.get("deployment_uuid"), str) or not item["deployment_uuid"]:
        raise CoolifyError("Unexpected deployment response; deployment UUID is missing.")
    status = safe_text(item.get("status"))
    return {"deployment_uuid": item["deployment_uuid"], "status": status,
            "outcome": DEPLOYMENT_OUTCOMES.get(status or "", "unknown"),
            "commit": safe_text(item.get("commit")),
            "commit_message": safe_text(item.get("commit_message")),
            "created_at": safe_text(item.get("created_at")),
            "updated_at": safe_text(item.get("updated_at"))}


def deployment_window(value, skip, take):
    """Split a history envelope into its total and the returned window.

    The history route is paginated server-side; a missing count, a bare
    list, or a window inconsistent with its total and limits is a shape
    failure, never a complete history.
    """
    if isinstance(skip, bool) or not isinstance(skip, int) or skip < 0:
        raise CoolifyError("Deployment history offset must be a non-negative integer.")
    if isinstance(take, bool) or not isinstance(take, int) or take < 1:
        raise CoolifyError("Deployment history limit must be a positive integer.")
    if not isinstance(value, dict) or not isinstance(value.get("deployments"), list):
        raise CoolifyError("Unexpected deployment history response; refusing to report a partial window as complete history.")
    total = value.get("count")
    if isinstance(total, bool) or not isinstance(total, int) or total < 0:
        raise CoolifyError("Unexpected deployment history response; total count is missing.")
    items = value["deployments"]
    if any(not isinstance(entry, dict) for entry in items):
        raise CoolifyError("Unexpected deployment history response; refusing to report a partial window as complete history.")
    if len(items) > take:
        raise CoolifyError("Inconsistent deployment history window; refusing to report it as a trustworthy page.")
    if skip >= total:
        if items:
            raise CoolifyError("Inconsistent deployment history window; refusing to report it as a trustworthy page.")
    elif not items or skip + len(items) > total:
        raise CoolifyError("Inconsistent deployment history window; refusing to report it as a trustworthy page.")
    return total, items


def scrub_token(value, token):
    """Remove a known Bearer [REDACTED] even if it is reflected in a display field."""
    if isinstance(value, str):
        return value.replace(token, "[redacted]") if token else value
    if isinstance(value, list):
        return [scrub_token(item, token) for item in value]
    if isinstance(value, dict):
        return {key: scrub_token(item, token) for key, item in value.items()}
    return value
