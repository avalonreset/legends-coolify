"""Fixed-endpoint GET client. No raw URL, mutation, redirect or secret-output lane."""
import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener


class CoolifyError(Exception):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


LISTS = {"applications", "databases", "services", "servers", "projects"}
DETAIL = re.compile(r"^/(applications|databases)/[A-Za-z0-9_-]{1,128}(?:/(envs|backups))?$")


def identifier(value):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", value or ""):
        raise CoolifyError("Invalid resource identifier; use the exact UUID from inventory.")
    return value


def allowed_path(path):
    if path in {"/health", "/version"} | {"/" + item for item in LISTS}:
        return True
    match = DETAIL.fullmatch(path)
    return bool(match and (match[2] is None or (match[1], match[2]) in {
        ("applications", "envs"), ("databases", "backups")
    }))


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
        if not token or any(c.isspace() for c in token):
            raise CoolifyError("Set COOLIFY_API_TOKEN to a read-permission token.")
        self.base_url = base_url.rstrip("/")
        self._token = token
        self.timeout = timeout
        # Avoid implicit credential routing through ambient proxy settings.
        self._opener = build_opener(ProxyHandler({}), NoRedirect())

    def get(self, path):
        if not allowed_path(path):
            raise CoolifyError("Endpoint is outside the read-only allowlist.")
        prefix = "/api" if path == "/health" else "/api/v1"
        req = Request(self.base_url + prefix + path, method="GET", headers={
            "Authorization": "Bearer " + self._token, "Accept": "application/json",
            "User-Agent": "legends-coolify/0.1.0",
        })
        try:
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
            raise CoolifyError(f"Coolify returned HTTP {error.code}; check API access, team scope and permissions. Response body omitted.") from None
        except (URLError, OSError, ValueError, UnicodeError):
            raise CoolifyError("Coolify request failed: verify network, TLS, instance URL and response format. Details omitted.") from None


def records(value):
    if isinstance(value, dict) and "data" in value:
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


def scrub_token(value, token):
    """Remove a known bearer token even if it is reflected in a display field."""
    if isinstance(value, str):
        return value.replace(token, "[redacted]") if token else value
    if isinstance(value, list):
        return [scrub_token(item, token) for item in value]
    if isinstance(value, dict):
        return {key: scrub_token(item, token) for key, item in value.items()}
    return value
