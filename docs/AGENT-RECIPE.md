# Operating legends-coolify

This is an on-demand module recipe, not a registered skill. The central `cto-legends` router owns discovery.

## Select knowledge first

Read `wiki/index.md`. Choose the runbook matching the requested outcome. Follow its source links when versions or deployment behavior matter. The vault is reusable knowledge; the user's own private workspace holds selected instance, team, resource IDs, evidence and decisions.

## Readiness

1. Run `legends-coolify doctor` (or `cto-legends run legends-coolify -- doctor`). This is offline and does not prove connectivity.
2. For authorized read-only work, ensure `COOLIFY_BASE_URL` and `COOLIFY_API_TOKEN` are supplied securely by the user's environment. No automatic secret-file loading.
3. Run `doctor --live`. A successful health page alone is insufficient; this also requires an authenticated application list.
4. Run the chosen command. Return its exact collection errors and limitations. If the API response shape differs, report it rather than calling missing data an empty success.

| Goal | Command | Interpretation |
|---|---|---|
| Inventory | `inventory` | Team-visible resources, selected fields only |
| Resource status | `health` | Container/resource state, not business function |
| Environment review | `env --uuid UUID` | Names and flags, no values |
| Database backups | `backups --uuid UUID` | Schedule metadata, not success or restore proof |
| Deployment planning | `plan --uuid UUID` | Advisory checklist only |

Reports go to a new private file with `--out PATH`, outside managed sources. Report names and UUIDs may still be sensitive. Do not upload reports to a public issue. Ask only for missing target or material authority, not routine read-only confirmation within an authorized task.

## Limits

- HTTPS instance origin only. Certificate verification stays enabled; redirects and implicit proxies are disabled.
- No generic endpoint runner, mutation flag, logs export, environment values, public app probing, remote shell or schema migration.
- Coolify versions differ. Current upstream permissions are documented in the vault; test the actual target version. Read permission is sufficient for this module's intended summaries.
- For execution outside this read-only module, select the official Coolify surface under the user's exact authorization. Do not pretend the advisory plan performed a change.

## Learn from the work

Keep the private receipt in the selected workspace. Propose a sanitized general lesson for `wiki/` with dated sources and a reproducible check; never copy raw incidents, secrets or client resource IDs into the distributed vault.
