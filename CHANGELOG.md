# Changelog

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
