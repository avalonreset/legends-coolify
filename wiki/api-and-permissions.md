# API and permissions

Coolify's protected API uses Bearer authentication. Tokens are bound to their creating user and team. Self-hosted instances also require API access to be enabled; IP restrictions can apply. A `401` commonly means invalid authentication, while `403` can indicate permissions, role, or instance access restrictions. Send the complete token value exactly as shown at creation, including its ID and separator. [Authorization](https://coolify.io/docs/api/authorization)

For this module, begin with a `read` token. Coolify distinguishes endpoint access from sensitive-field access: `read:sensitive` exposes supported sensitive content, and `root` provides broader authority. Neither is needed for the module's intended inventory summaries. A separate `deploy` permission covers deployment triggers, and only recognized permissions are accepted. Do not solve a failed read by reflexively increasing privilege. Check team, endpoint support, version, and permission scope first. [Permissions](https://coolify.io/docs/api/permissions)

Store the complete credential in the caller's secret store or process environment. Never put it in a command argument, URL, transcript, example, or receipt. The module uses `COOLIFY_API_TOKEN` and `COOLIFY_BASE_URL`; consult the repository usage instructions for accepted URL syntax.

An allowlisted output schema reduces accidental disclosure; it does not make every name or identifier public. Handle inventory as private operational data. Treat unexpected response shapes as incomplete evidence rather than printing the raw payload.

See [inventory and health](inventory-and-health.md), [troubleshooting](troubleshooting.md), [lifecycle and versions](paas-lifecycle-and-versions.md), and [sources S01-S03, S16](../references/sources.md).
