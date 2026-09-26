# Public and private boundaries

This repository publishes reusable practice. It is not a home for an operator's infrastructure inventory.

| Public module | Private operator workspace or secret store |
| --- | --- |
| Cited product behavior | Instance URLs, server addresses, resource UUIDs |
| Placeholder examples | Real service names and topology |
| Sanitized lessons and checklists | Raw API payloads and logs |
| Blank receipt templates | Deployment receipts and recovery evidence |
| Credential variable names | Tokens, keys, passwords and connection strings |

Create operational receipts outside the public checkout. The [receipt template](../templates/private-operation-receipt.md) is safe because it is blank. A completed receipt may be sensitive even when it contains no credentials.

Only promote a lesson after removing identifiers, checking quoted output, separating observation from inference, and ensuring the claim still holds without private context. A public source update should explain the transferable behavior and cite its evidence, not reproduce an incident log.

Do not copy old private implementation files into the public project wholesale. Reimplement the small portable behavior and preserve sensitive history in its original authorized location.

See [maintenance](knowledge-maintenance.md) and [overview](overview.md).
