# Privacy

`legends-coolify` is local-first, strictly read-only, and includes no telemetry, analytics, or background network activity.

## Offline by default

- `legends-coolify doctor` (without `--live`) and `legends-coolify resources` run completely offline.
- Packaged documentation, `wiki/` references, and `knowledge/coolify/` runbooks are resolved from the local installation without network requests.

## Explicit Coolify API egress

- Live read-only commands (`doctor --live`, `inventory`, `health`, `env`, `backups`, `deployments`, `plan`) connect exclusively over verified HTTPS (`GET` only) to the caller's `COOLIFY_BASE_URL` using `COOLIFY_API_TOKEN` from the environment.
- Ambient proxy environment variables (`HTTP_PROXY`, `HTTPS_PROXY`) and HTTP redirects (`301`, `302`, `303`, `307`, `308`) are refused so Bearer credentials are never forwarded off-origin.
- Loopback, unspecified, multicast, and link-local metadata addresses (`169.254.0.0/16`, `fe80::/10`) are always refused; private RFC1918, ULA, and Tailscale ranges are refused unless `--allow-private-host` (or `COOLIFY_ALLOW_PRIVATE_HOST=1`) is explicitly supplied.
- Environment variable values, deployment logs, raw API tokens, and provider error payloads are never exported or printed to stdout, stderr, or `--out` report files.

See [SECURITY.md](SECURITY.md) for vulnerability reporting and credential hygiene rules.
