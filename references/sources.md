# Source ledger

Reviewed: **2026-09-26**. All sources below were retrieved during initial research. Coolify documentation is rolling documentation; a retrieval date does not establish compatibility with every installed version. The source URLs are canonical public references, not copies of their content.

| ID | Source | Claim coverage | Used in |
| --- | --- | --- | --- |
| S01 | [Coolify API overview](https://coolify.io/docs/api/overview) | API base path; public health endpoint versus protected resources | [Health](../wiki/inventory-and-health.md) |
| S02 | [API authorization](https://coolify.io/docs/api/authorization) | Bearer tokens; user/team binding; self-hosted API access; 401/403 interpretation | [API](../wiki/api-and-permissions.md) |
| S03 | [API permissions](https://coolify.io/docs/api/permissions) | Read and sensitive-read separation; least privilege; role/team restrictions | [API](../wiki/api-and-permissions.md) |
| S04 | [Health checks](https://coolify.io/docs/applications/configuration/health-checks) | Internal probes, clients in images, Compose checks and Traefik readiness | [Health](../wiki/inventory-and-health.md) |
| S05 | [Application configuration](https://coolify.io/docs/applications/configuration/overview) | Saved configuration versus applied runtime; build versus runtime changes | [Deployment](../wiki/deployment-and-rollback.md) |
| S06 | [Rollbacks](https://coolify.io/docs/applications/deployments/rollbacks) | Image retention and rollback limits; state and current configuration | [Deployment](../wiki/deployment-and-rollback.md) |
| S07 | [Application operations](https://coolify.io/docs/applications/operations/overview) | Deployment output versus runtime logs | [Deployment](../wiki/deployment-and-rollback.md), [Troubleshooting](../wiki/troubleshooting.md) |
| S08 | [Instance backup](https://coolify.io/docs/core/backup-and-recovery/instance-backup) | Control-plane scope and separate APP_KEY recovery requirement | [Backups](../wiki/backups-and-restore.md) |
| S09 | [Instance restore](https://coolify.io/docs/core/backup-and-recovery/instance-restore) | Host recovery prerequisites and excluded workload data | [Backups](../wiki/backups-and-restore.md) |
| S10 | [Database restore](https://coolify.io/docs/databases/restore) | Engine support; stopping writers; import validation | [Backups](../wiki/backups-and-restore.md), [Migration](../wiki/migration-and-single-writer.md) |
| S11 | [Environment variables](https://coolify.io/docs/applications/configuration/environment-variables) | Build/runtime/preview/shared configuration and applying changes | [Environment](../wiki/environment-tls-cors.md) |
| S12 | [Domains](https://coolify.io/docs/core/networking/domains) | DNS, proxy routing, internal ports and automatic TLS prerequisites | [Environment](../wiki/environment-tls-cors.md) |
| S13 | [Troubleshooting](https://coolify.io/docs/troubleshoot) | Gateway, certificate and server-validation diagnostic entry points | [Troubleshooting](../wiki/troubleshooting.md) |
| S14 | [MDN CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS) | Browser origin enforcement, preflight and credentialed-origin restrictions | [Environment](../wiki/environment-tls-cors.md) |

## Interpretation and limits

The evidence-layer model, single-writer migration checklist, private/public separation, and knowledge update loop are module recommendations. They synthesize operational reasoning and the cited constraints; they are not promises made by Coolify.

No private incident receipt is included as a public source. No successful restore, deployment, or public-router discovery is inferred from these documentation reads. Reverify version-sensitive details against the target version before a consequential operation.

Use the [source update template](../templates/source-update.md) for revisions. Return to the [vault index](../wiki/index.md).
