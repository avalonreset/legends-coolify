# Deployment and rollback

The module's `plan --uuid` produces read-only advice. Actual changes require a separate authorized operator workflow.

Before a deployment, identify the exact resource, immutable source or image revision, configuration changes, state changes, acceptance check, and recovery boundary. Record these privately. Preserve an available known-good image and account for its compatibility with current runtime settings.

Saving configuration does not necessarily update a running container. Build inputs and runtime settings have different application paths; consult the deployed version's guidance before choosing a deploy or restart. [Configuration overview](https://coolify.io/docs/applications/configuration/overview)

## Rollback has limits

An application rollback selects an older retained image. It does not reverse database migrations or restore volumes and external state. Current runtime settings still matter, and image cleanup can remove the desired rollback target. Verify schema compatibility and a separate data recovery plan before promising a quick rollback. [Rollbacks](https://coolify.io/docs/applications/deployments/rollbacks)

Define acceptance before acting: route, readiness, representative user flow, data correctness, and relevant worker behavior. During an incident, compare the first failing deployment step with runtime logs; build failures and application failures are different evidence streams. [Operations](https://coolify.io/docs/applications/operations/overview)

See [backups](backups-and-restore.md), [single-writer migration](migration-and-single-writer.md), and [private receipt](../templates/private-operation-receipt.md).
