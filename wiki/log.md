# Knowledge log

## 2026-10-10: deployment status reads

Covered the `deployments` command (running list, bounded history with `--limit`/`--skip`, single by UUID) in the [deployment note](deployment-and-rollback.md), the [vault index](index.md), and the [agent recipe](../docs/AGENT-RECIPE.md). Route shapes, `read` ability, skip/take behavior, and the `{count, deployments}` envelope are pinned to Coolify v4.4.6 in ledger sources S20-S22 ([sources](../references/sources.md)). Rebuilt the optional Empire knowledge pack from current sources after the QA staging deletion.

Evidence level: documentation and pinned upstream source reviewed. This entry does not attest to live deployments, backup execution, restore drills, router distribution, or Brainstein audit completion.

## 2026-10-10: second source review plus lifecycle and boundary notes

Re-read all fourteen original sources; every URL still resolves and supports its claims, with behavior refinements noted in the [source ledger](../references/sources.md). Added a migration source, the release-notes feed, two Hetzner app sources, and the Empire knowledge-packs contract. Added [PaaS lifecycle and version drift](paas-lifecycle-and-versions.md) and [Coolify and Hetzner boundary](coolify-hetzner-boundary.md); strengthened health-versus-status, backup-versus-restore, permission, and troubleshooting notes from the re-read. Shipped the optional Empire knowledge pack under `knowledge/coolify/`.

Evidence level: documentation reviewed. This entry does not attest to live backups, restore drills, deployment success, router distribution, or Brainstein audit completion.

## 2026-09-26: initial public baseline

Created linked guidance and a dated source ledger from current official Coolify documentation and MDN's CORS reference. Added templates for private operational receipts and public source updates. Kept house infrastructure and earlier private implementation outside this vault.

Evidence level: documentation reviewed. This entry does not attest to live backups, restore drills, deployment success, router distribution, or Brainstein audit completion.

Return to [index](index.md).
