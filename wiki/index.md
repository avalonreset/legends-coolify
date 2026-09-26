# legends-coolify knowledge vault

Reusable operational knowledge for agents and people working with Coolify. Open the repository folder as an Obsidian vault, or follow these links in GitHub. No Obsidian plugins are required.

Start with [Overview](overview.md), [Current focus](hot.md), and the [source ledger](../references/sources.md). This is a researched starting vault, not a claim of production certification or complete Coolify coverage.

| Task | Read | Tool support |
| --- | --- | --- |
| Connect safely | [API and permissions](api-and-permissions.md) | `doctor` checks local readiness |
| Understand resources | [Inventory and health](inventory-and-health.md) | `inventory`, `health` |
| Review configuration | [Environment, TLS and CORS](environment-tls-cors.md) | `env --uuid` lists names only |
| Prepare a change | [Deployment and rollback](deployment-and-rollback.md) | `plan --uuid` is advisory |
| Assess recoverability | [Backups and restore](backups-and-restore.md) | `backups --uuid` reads schedule metadata |
| Move a workload | [Migration and single writer](migration-and-single-writer.md) | Read-only evidence plus private plan |
| Investigate failure | [Troubleshooting](troubleshooting.md) | Compare independent evidence layers |
| Improve the knowledge | [Maintenance](knowledge-maintenance.md) | [Source update template](../templates/source-update.md) |

Keep real deployment details outside this public vault. Read [Public and private boundaries](public-private-boundaries.md) before saving a receipt. See the [change log](log.md) for knowledge changes.
