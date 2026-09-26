# Migration and single writer

This is module operational guidance, not an upstream Coolify guarantee. It generalizes stateful migration risks; it is not a transcript of a private production migration.

A healthy destination copy is insufficient to declare cutover. Two active writers can diverge data or duplicate jobs, notifications, billing, and webhook processing. DNS changes alone do not stop old background workers.

## Prepare a bounded migration plan

1. Inventory the application, database, mounts, object storage, schedules, workers, webhooks, ingress, and external dependencies privately.
2. Identify the authoritative writer and the exact mechanism for quiescing every other writer.
3. Verify recovery artifacts and compatibility. Define the data synchronization window and abort conditions.
4. Prepare the destination without activating outbound effects. Validate its revision, configuration, data, and internal behavior.
5. In the authorized cutover window, quiesce source writers, perform the final state transfer, and enable the selected destination writer.
6. Verify ingress plus a representative transaction and worker behavior. Keep the source recoverable until the retention decision is explicit.

After the destination accepts writes, reverting traffic may lose or split data. A rollback plan must explain how destination writes are reconciled. Do not advertise instant rollback when only an image or DNS record can be reversed.

The single-writer boundary and reconciliation policy are recommendations. Coolify's documented restore workflow also requires stopping application writes before import. [Database restore](https://coolify.io/docs/databases/restore)

Use [deployment planning](deployment-and-rollback.md), [backup evidence](backups-and-restore.md), and the [private receipt template](../templates/private-operation-receipt.md). The CLI does not execute this checklist.
