# 0.1.0 validation

Checked 2026-09-26.

- Windows, Python 3.11: 19 offline tests passed, covering endpoint restrictions, redirects, HTTPS origins, redaction, error handling, malformed records, target identity, partial collections and report preservation.
- Public-source checks passed: required files, Markdown links, naming punctuation and private-residue patterns.
- An independent code review found a malformed-resource response that could be treated as a successful plan. The release now requires a matching target UUID; regression tests cover incomplete list rows and mismatched plans.
- Authorized read-only calls against Coolify 4.3.14 completed: authenticated doctor, inventory, resource status, application environment names, advisory plan and database backup schedules. Both empty and nonempty backup schedules were observed. No infrastructure changes were performed.
- All live evidence remains private. These results do not certify application health, successful backups, restore capability, write operations or every Coolify version.

Cross-platform installation and offline checks run in the repository's GitHub Actions matrix. Consult the checks attached to the release commit for their result. Only Windows live API use was tested for this first release.

The [source ledger](../references/sources.md) separately records the researched knowledge baseline. This release does not claim a Brainstein certification or a completed disaster recovery drill.
