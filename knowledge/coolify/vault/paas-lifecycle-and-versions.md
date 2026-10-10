# PaaS lifecycle and version drift

Coolify ships fast and documents a rolling surface. This note explains how to plan a PaaS lifecycle (deploy, operate, migrate) without assuming that today's validated behavior matches tomorrow's release.

## Version drift is normal

The source review on 2026-10-10 found ten Coolify releases between v4.3.21 (2026-09-15) and v4.4.6 (2026-10-09), including minor 4.4.0. That window added API-visible behavior changes, for example a `deploy` permission requirement for `instant_deploy`, rejection of unknown token permissions and of `host_path` in volume requests, new PostgreSQL restore options, and 409 rejection of concurrent database imports. [Release notes](https://github.com/coollabsio/coolify/releases)

Consequences for this module:

- Record the target Coolify version privately before any consequential reading. A receipt without a version cannot be compared with later behavior.
- Treat the 0.1.0 live validation target (Coolify 4.3.14) as dated evidence, not a compatibility promise for 4.4.x.
- When the API response shape differs from the documented one, report it as incomplete evidence rather than calling missing data an empty success. The CLI already refuses unexpected shapes instead of guessing.
- Recheck permission, schema, backup, and rollback guidance against the installed version before relying on it. See [maintenance](knowledge-maintenance.md).

## Lifecycle planning

Coolify separates image preparation from container replacement. Saving configuration updates stored settings; deploy, redeploy, restart, and rollback each recreate runtime state through different paths with different cache and image behavior. [Configuration overview](https://coolify.io/docs/applications/configuration/overview)

Plan each lifecycle step with its own acceptance and recovery boundary:

1. **Deploy.** Name the exact resource, immutable source or image revision, configuration changes, and the user flow that proves success. Use [deployment and rollback](deployment-and-rollback.md).
2. **Operate.** Know which log answers which question: deployment logs for build and rollout failures, runtime logs for application failures. Viewing container logs needs resource-update permission; API log reads need `read:sensitive` or `root`. Metrics need Sentinel and are unavailable for Compose applications. [Application operations](https://coolify.io/docs/applications/operations/overview)
3. **Move within an instance.** Clone or move resources between projects, environments, and destinations on the same control plane through Resource Operations.
4. **Move between instances.** Coolify provides no single export/import for an application: recreate the application on the destination, verify it on a temporary domain, move each stateful dependency through its own supported path, then transfer traffic after a final sync with writes stopped. [Migrate an application](https://coolify.io/docs/applications/operations/migrate-between-instances)
5. **Recover.** Instance backup, workload backup, and restore testing are separate evidence items. See [backups and restore](backups-and-restore.md).

This module stays read-only through all five steps: it collects bounded evidence and advisory plans. Execution belongs to an explicitly authorized operator workflow under the user's exact authorization, never to the advisory plan itself.

See [migration and single writer](migration-and-single-writer.md) for the writer-ownership rule that every move must satisfy, and [sources S05, S07, S15-S16](sources.md).
