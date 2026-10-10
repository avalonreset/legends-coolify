# Deployment and rollback

The module's `plan --uuid` produces read-only advice. Actual changes require a separate authorized operator workflow.

Before a deployment, identify the exact resource, immutable source or image revision, configuration changes, state changes, acceptance check, and recovery boundary. Record these privately. Preserve an available known-good image and account for its compatibility with current runtime settings.

Saving configuration does not necessarily update a running container. Build inputs and runtime settings have different application paths; consult the deployed version's guidance before choosing a deploy or restart. Restart recreates the runtime through the deployment queue: source-based paths reuse an eligible image while Docker Image paths pull the saved reference again. [Configuration overview](https://coolify.io/docs/applications/configuration/overview)

## Rollback has limits

An application rollback selects an older retained image. It does not reverse database migrations or restore volumes and external state. Current runtime settings still matter, and image cleanup can remove the desired rollback target. Verify schema compatibility and a separate data recovery plan before promising a quick rollback. [Rollbacks](https://coolify.io/docs/applications/deployments/rollbacks)

Define acceptance before acting: route, readiness, representative user flow, data correctness, and relevant worker behavior. During an incident, compare the first failing deployment step with runtime logs; build failures and application failures are different evidence streams. [Operations](https://coolify.io/docs/applications/operations/overview)

## Deployment status reads

The `deployments` command covers three read-only views. Route shapes and the `read` ability are pinned to Coolify v4.4.6 ([routes](https://github.com/coollabsio/coolify/blob/v4.4.6/routes/api.php), [controller](https://github.com/coollabsio/coolify/blob/v4.4.6/app/Http/Controllers/Api/DeployController.php), [history shape](https://github.com/coollabsio/coolify/blob/v4.4.6/app/Models/Application.php)); reverify after version drift.

| Goal | Command | Reads |
| --- | --- | --- |
| Running list | `deployments` | Queued and in-progress deployments only; never finished history |
| Bounded history | `deployments --uuid UUID [--limit N] [--skip M]` | Newest-first window of one application's retained deployments with `total_count`, `returned_count`, and `has_more`; `--limit` 1-50 (default 10), `--skip` 0-100000 (default 0) |
| Single deployment | `deployments --deployment-uuid UUID` | One deployment by UUID; the response UUID must match the request |

Each entry carries selected metadata only: deployment UUID, status, outcome (`active`, `finished`, `failed`, `cancelled`, or `unknown` for a future status), commit, commit message, and created/updated timestamps. Logs are excluded: upstream withholds them from `read` tokens and the module whitelist drops them regardless. A history window is not complete history; page with `--skip` while `has_more` is true. Cancelling a deployment is a separate `deploy`-ability POST and stays outside this module.

See [backups](backups-and-restore.md), [single-writer migration](migration-and-single-writer.md), and [private receipt](../templates/private-operation-receipt.md).
