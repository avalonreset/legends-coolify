# Troubleshooting

Start with one concrete failure, its timestamp, and the last known working state. Choose a check that distinguishes likely causes before changing anything.

| Symptom | Next evidence | Avoid assuming |
| --- | --- | --- |
| API `401` | Token validity and team membership | Instance is down |
| API `403` | Permission, role, API switch and IP restrictions | Root access is required |
| Empty inventory | Token team and endpoint scope | No workloads exist |
| API reachable, app fails | Resource status, route and internal readiness | Platform health means app health |
| Deployment fails | First failed build/pull step | Runtime restart fixes a build |
| App crashes after deployment | Timestamped container logs and dependency readiness | Build success proves correct runtime |
| Public `502` | Internal port, bind address and upstream reachability | DNS alone is responsible |
| Public `503` | Health and available routing targets | Container existence means readiness |
| Browser fails, CLI succeeds | CORS, preflight, cookie/origin behavior | TLS must be broken |
| Backups configured, recovery unknown | Execution, artifact access, restore drill | Schedule proves recoverability |

The HTTP symptom rows are hypotheses, not unique diagnoses. Coolify's [troubleshooting index](https://coolify.io/docs/troubleshoot) has focused guides for gateway failures, certificate problems, server validation, 504 timeouts, dashboard access, and server-side failures. [Application operations](https://coolify.io/docs/applications/operations/overview) separates deployment output from runtime logs.

Record a sanitized conclusion and the check that supported it. Keep raw logs private and inspect for secrets before any sharing. If upstream and live behavior conflict, record the version and uncertainty, then update the [source ledger](sources.md) through [maintenance](knowledge-maintenance.md).
