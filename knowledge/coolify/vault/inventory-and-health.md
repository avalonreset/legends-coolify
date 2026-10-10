# Inventory and health

Inventory establishes which objects a token can see. It is not an inventory of every team or every external dependency. Keep applications, databases, and services distinct; a service can contain multiple components.

## Separate the layers

| Observation | What it supports | What it does not prove |
| --- | --- | --- |
| Local `doctor` passes | Local module prerequisites pass | Connectivity or production readiness |
| Coolify API health responds | Control-plane endpoint reachable | Protected API access or app availability |
| Protected inventory succeeds | Credential can read those resources | Completeness across teams |
| Resource status reports running | Reported workload state | Public TLS, browser behavior, or correct data |
| Internal readiness check succeeds | Configured probe passes | Complete user journey |
| Public request succeeds | That route works from that vantage point | Login, writes, jobs, or recovery |

Coolify exposes unauthenticated health endpoints separately from protected resource APIs. [API overview](https://coolify.io/docs/api/overview)

For application checks, verify the probe's internal port and command inside the final container. HTTP probes need an installed client. Compose workloads define their own component checks. With Traefik, failed application health can remove routing targets; when every container is unhealthy, Traefik can return 404 or No available server instead of forwarding. A passing container status is therefore not proof of application health. The generated HTTP check judges only the probe client exit status, not the Expected code or Expected response text fields. [Health checks](https://coolify.io/docs/applications/configuration/health-checks)

Use a private [receipt](templates/private-operation-receipt.md) to record timestamp, version, scope, observed layers, and unknowns. Do not translate `health` command success into a blanket healthy-system claim. Follow [troubleshooting](troubleshooting.md) for the next discriminating check.
