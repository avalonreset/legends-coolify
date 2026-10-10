# Current focus

Knowledge baseline: 2026-10-10 (second review; first baseline 2026-09-26).

The vault covers safe inspection and planning across API access, health, configuration, recovery, migration, lifecycle planning, and the server/PaaS boundary. It contains no private infrastructure inventory and no production execution receipts.

Before declaring a target ready, record its version privately, run the implemented checks, and identify unsupported or unobserved evidence explicitly. Backup schedule metadata alone does not prove recoverability. API reachability alone does not prove application health. Coolify shipped ten releases between the two baselines, so version-qualified reading matters more than before.

Next knowledge improvements should follow real user failures or an upstream behavior change. Priorities are tested restore case studies and engine-specific recovery notes, followed by version-qualified API compatibility evidence. Publish only sanitized, reusable findings.

See [maintenance](knowledge-maintenance.md), [source ledger](sources.md), and [log](log.md).
