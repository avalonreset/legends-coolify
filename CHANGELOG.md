# Changelog

## 0.2.3 - 2026-11-11

- Enforce DNS resolution and IP pinning in `legends_coolify/client.py`: always block loopback, unspecified, multicast, and link-local metadata (`169.254.0.0/16`, `fe80::/10`) targets, and reject private RFC1918, ULA, and Tailscale/CGNAT addresses unless `--allow-private-host` (`COOLIFY_ALLOW_PRIVATE_HOST=1`) is explicitly supplied.
- Enforce full ancestor-chain symlink/junction refusal (`check_no_symlink_chain` with macOS `/var`, `/tmp`, `/etc` allowance) and Windows Controlled Folder Access (CFA) directory protection on `--out` report paths in `legends_coolify/cli.py`.
- Remove founder path residue in `docs/KNOWLEDGE-PACK.md`, document `legends-coolify resources` and `--allow-private-host` in `docs/AGENT-RECIPE.md` and `AGENTS.md`, and fix CommonMark code-span backtick formatting in `CHANGELOG.md`.
- Add `PRIVACY.md` and include `.legends-router-pin`, `CODE_OF_CONDUCT.md`, and `PRIVACY.md` across `MANIFEST.in`, `setup.py` wheel `_data/` mirroring, and `scripts/check_release.py`.

## 0.2.2 - 2026-11-05

- Add `.legends-module`, `docs/router-provenance.json`, and `THIRD_PARTY_NOTICES.md`, remove duplicate `NOTICE.md` and tracked `.obsidian/app.json`, and standardize the ``## Agent setup (via `cto-legends`)`` section in `README.md`.
- Upgrade `scripts/check_release.py`, `AGENTS.md`, and `docs/AGENT-RECIPE.md` with Windows Defender / EDR anti-ransomware guardrails and knowledge pack hash verification.
- Pin `avalonreset/legends-empire` `v0.3.4` (`1ede96ad670b60b215b66457369691da6c61d017`) and `pip>=26.2.2` in `.github/workflows/checks.yml`.

## 0.2.1 - 2026-10-29

- Raise minimum supported Python runtime to Python 3.11 (`requires-python = ">=3.11"`) across package metadata, documentation, and multi-OS CI.
- Harden `.github/workflows/checks.yml` with 40-character commit SHA action pins and upgrade `pip>=26.2.2` before package installation.

## 0.2.0 - 2026-10-10

- Inspect running deployments, bounded application deployment history and a
  selected deployment without exporting logs or executing changes.
- Reject malformed readiness responses and incomplete list envelopes instead
  of treating them as successful collections. Validate deployment identity
  and history windows.
- Improve HTTP error guidance, credential validation and report-file handling.

- Package the source-cited knowledge library and agent instructions with the
  wheel; expose installed resource paths without requiring credentials.
- Add an optional versioned Empire knowledge pack with explicit reference
  ownership, private-note preservation and conflict-aware updates.
- Refresh official-source guidance and explain the provider/platform boundary
  between Legends Hetzner and Coolify.
- Expand cross-platform artifact and knowledge-attachment verification.
- Improve generic onboarding, repository presentation and release procedures,
  including researched metadata and verified social-preview publication.

The module remains read-only. Deployment plans are advisory, resource status
does not certify application health, and backup metadata does not prove restore
capability. Empire attachment is optional and never occurs during installation.

## 0.1.0 - 2026-09-26

- First portable public edition of legends-coolify.
- Source-cited Coolify vault with reusable operational runbooks and private-record templates.
- Standard-library read-only CLI for inventory, resource status, environment names, backup schedules and advisory deployment planning.
- Offline and authenticated live doctor; explicit partial collection failures.
- Fixed GET allowlist, verified HTTPS, no redirects, names-only environment reports, bounded responses and no provider error-body output.
- Central CTO router recipe; no standalone module skill registration.

The earlier private PowerShell house implementation remains separate. This release does not deploy or modify resources.
