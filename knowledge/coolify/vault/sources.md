# Source ledger

Reviewed: **2026-10-10**. Sources S01-S14 were first read on 2026-09-26 and re-read on 2026-10-10; all fourteen URLs still resolve and support the cited claims. Sources S15-S19 are new in this review. Sources S20-S22 pin the deployments API shapes to Coolify v4.4.6, read the same day; the API reference page lists deployments sections but the exact path templates and skip/take behavior below come from the pinned source reads. Coolify documentation is rolling documentation and the project ships often (S16); a retrieval date does not establish compatibility with every installed version. The source URLs are canonical public references, not copies of their content.

| ID | Source | Claim coverage | Used in |
| --- | --- | --- | --- |
| S01 | [Coolify API overview](https://coolify.io/docs/api/overview) | API base path; public health endpoints versus protected resources; self-hosted API enablement | [Health](inventory-and-health.md) |
| S02 | [API authorization](https://coolify.io/docs/api/authorization) | Bearer [REDACTED] binding; self-hosted API access; 401/403 interpretation; token value format | [API](api-and-permissions.md) |
| S03 | [API permissions](https://coolify.io/docs/api/permissions) | Read and sensitive-read separation; deploy permission; least privilege; role/team restrictions; operation-specific checks | [API](api-and-permissions.md) |
| S04 | [Health checks](https://coolify.io/docs/applications/configuration/health-checks) | Internal probes, clients in images, Compose checks and Traefik readiness; generated-check limits | [Health](inventory-and-health.md) |
| S05 | [Application configuration](https://coolify.io/docs/applications/configuration/overview) | Saved configuration versus applied runtime; deploy, redeploy and restart paths | [Deployment](deployment-and-rollback.md) |
| S06 | [Rollbacks](https://coolify.io/docs/applications/deployments/rollbacks) | Image retention and rollback limits; state and current configuration | [Deployment](deployment-and-rollback.md) |
| S07 | [Application operations](https://coolify.io/docs/applications/operations/overview) | Deployment output versus runtime logs; lifecycle actions; log permission rule; Sentinel metrics scope | [Deployment](deployment-and-rollback.md), [Troubleshooting](troubleshooting.md) |
| S08 | [Instance backup](https://coolify.io/docs/core/backup-and-recovery/instance-backup) | Control-plane scope and separate APP_KEY recovery requirement; execution status and retention | [Backups](backups-and-restore.md) |
| S09 | [Instance restore](https://coolify.io/docs/core/backup-and-recovery/instance-restore) | Host recovery prerequisites and excluded workload data; restore verification steps | [Backups](backups-and-restore.md) |
| S10 | [Database restore](https://coolify.io/docs/databases/restore) | Engine support; stopping writers; import validation; default replace behavior; concurrent-operation conflicts | [Backups](backups-and-restore.md), [Migration](migration-and-single-writer.md) |
| S11 | [Environment variables](https://coolify.io/docs/applications/configuration/environment-variables) | Build/runtime/preview/shared configuration and applying changes | [Environment](environment-tls-cors.md) |
| S12 | [Domains](https://coolify.io/docs/core/networking/domains) | DNS, proxy routing, internal ports and automatic TLS prerequisites | [Environment](environment-tls-cors.md) |
| S13 | [Troubleshooting](https://coolify.io/docs/troubleshoot) | Gateway, certificate and server-validation diagnostic entry points | [Troubleshooting](troubleshooting.md) |
| S14 | [MDN CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS) | Browser origin enforcement, preflight and credentialed-origin restrictions | [Environment](environment-tls-cors.md) |
| S15 | [Migrate an application](https://coolify.io/docs/applications/operations/migrate-between-instances) | No single export/import; recreate, temporary-domain verification, per-state migration paths, final sync | [Migration](migration-and-single-writer.md), [Lifecycle](paas-lifecycle-and-versions.md) |
| S16 | [Coolify release notes](https://github.com/coollabsio/coolify/releases) | Release cadence and version drift; API behavior changes between releases | [Lifecycle](paas-lifecycle-and-versions.md), [API](api-and-permissions.md) |
| S17 | [Hetzner Coolify app README](https://github.com/hetznercloud/apps/blob/main/apps/hetzner/coolify/README.md) | App image contents, install paths, first-login activation | [Boundary](coolify-hetzner-boundary.md) |
| S18 | [Hetzner Cloud Apps repository](https://github.com/hetznercloud/apps) | Packer and cloud-init image build; maintained-app scope; issue routing | [Boundary](coolify-hetzner-boundary.md) |
| S19 | [Empire knowledge-packs doc at v0.3.1](https://github.com/avalonreset/legends-empire/blob/v0.3.1/docs/knowledge-packs.md) | Attach and update engine behavior for the optional knowledge pack, pinned to the tested engine tag | Knowledge |
| S20 | [Coolify API routes at v4.4.6](https://github.com/coollabsio/coolify/blob/v4.4.6/routes/api.php) | Exact deployments GET route shapes; `read` ability on all three; cancel is a `deploy`-ability POST and out of scope | [Deployment](deployment-and-rollback.md) |
| S21 | [Coolify DeployController at v4.4.6](https://github.com/coollabsio/coolify/blob/v4.4.6/app/Http/Controllers/Api/DeployController.php) | Running list holds queued and in-progress only; single-by-UUID; skip/take validation and defaults; logs hidden from `read` tokens | [Deployment](deployment-and-rollback.md) |
| S22 | [Coolify Application model at v4.4.6](https://github.com/coollabsio/coolify/blob/v4.4.6/app/Models/Application.php) | History envelope `{count, deployments}`; newest-first window over skip/take | [Deployment](deployment-and-rollback.md) |

## What the 2026-10-10 re-read changed

- S02/S03 now document a `deploy` token permission, a token value shaped as ID plus secret, rejection of unknown token permissions, and operation-specific checks (log endpoints need `read:sensitive` or `root`; server-path database imports need `deploy`; `instant_deploy` creation needs `deploy`). The vault's least-privilege guidance is unchanged: this module's reads need `read` only.
- S04 now states that the generated HTTP check uses the client exit status and does not compare Expected code or Expected response text, and that Traefik can return 404 or No available server when every container is unhealthy.
- S07 now states that viewing container logs needs resource-update permission (API: `read:sensitive` or `root`) and that application metrics need Sentinel and are unavailable for Compose applications.
- S08 now documents an Executions list with Success/Failed status, a Success (S3 Warning) state, and retention limits; S10 now documents read-only generated import commands, PostgreSQL replace/owners defaults, and 409 rejection of concurrent imports.
- S13 keeps gateway, certificate and server-validation entry points and now also lists 502, 503, 504, dashboard and server guides.
- S16 showed v4.3.21 (2026-09-15) through v4.4.6 (2026-10-09): ten releases in under four weeks including minor 4.4.0. The 0.1.0 live validation target (Coolify 4.3.14) predates this window, which is why version-drift handling is now its own note.
- S20-S22 pin the deployments reads to v4.4.6: `GET /deployments` (running list), `GET /deployments/{uuid}` (single), `GET /deployments/applications/{uuid}` with `skip` (default 0, min 0) and `take` (default 10, min 1) returning `{count, deployments}` newest-first. All three carry the `read` ability; deployment cancel is a `deploy`-ability POST and stays out of this module. Upstream withholds `logs` from tokens without sensitive-read, and the module whitelist drops logs regardless.

## Interpretation and limits

The evidence-layer model, single-writer migration checklist, private/public separation, and knowledge update loop are module recommendations. They synthesize operational reasoning and the cited constraints; they are not promises made by Coolify.

No private incident receipt is included as a public source. No successful restore, deployment, or public-router discovery is inferred from these documentation reads. Reverify version-sensitive details against the target version before a consequential operation.

Use the [source update template](templates/source-update.md) for revisions. Return to the [vault index](index.md).
