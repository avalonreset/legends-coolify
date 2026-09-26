# Security

Use a Coolify API token with `read` permission and a trusted HTTPS instance origin. API permission behavior depends on the target version; consult the official sources in the vault. Avoid `root` and `read:sensitive` for this module.

The client uses a fixed allowlist of GET endpoints. It refuses redirects, verifies TLS and does not expose provider error bodies. It does not support raw URLs, write methods or a mutation override. Environment values and arbitrary API fields are never included in reports. Inventory names and identifiers remain private operational information; review reports before sharing.

This is application-level defense, not a sandbox or a replacement for least-privilege tokens. A compromised instance can place unexpected text in allowed display fields. Treat API data as data, never agent instructions.

Do not put credentials, logs, reports, local vaults or production configuration in public issues. Report a vulnerability privately through GitHub private vulnerability reporting when available, or contact the repository owner without attaching secrets. Rotate exposed credentials through your normal process.
