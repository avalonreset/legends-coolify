# Backups and restore

`backups --uuid` inspects schedule metadata. A configured or enabled schedule is not proof that a backup ran, that an artifact is readable, or that restoration works.

Track recovery as separate evidence: configured schedule, successful execution, retained accessible artifact, and tested restore. Record the last verified dates and recovery objectives privately. Unknown evidence remains unknown.

## Three scopes

| Scope | What needs its own plan |
| --- | --- |
| Coolify instance | Control-plane database and recovery prerequisites |
| Workload database | Engine-compatible dump, retention, and tested import |
| Application storage | Volumes, bind mounts, object storage, and external state |

The Coolify instance backup does not contain workload data. Preserve `APP_KEY` in a secure recovery store separately; it is required to read restored encrypted secrets. Never copy it into this vault. [Instance backup](https://coolify.io/docs/core/backup-and-recovery/instance-backup)

Instance recovery has additional prerequisites when moving hosts, including SSH material and version context. Restoring the control plane does not restore application volumes. [Instance restore](https://coolify.io/docs/core/backup-and-recovery/instance-restore)

For a workload restore, verify engine/version compatibility and stop writes, including workers and schedules. Validate representative data before reconnecting writers. Built-in import support varies by database engine. [Database restore](https://coolify.io/docs/databases/restore)

Module recommendation: test restoration into an isolated target, with outbound notifications and jobs disabled, before relying on a recovery plan. Measure the achieved recovery time and data loss window. The CLI does not perform these operations.

See [migration](migration-and-single-writer.md) and [private receipt](../templates/private-operation-receipt.md).
