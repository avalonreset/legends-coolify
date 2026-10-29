# Validation

## 0.2.1

Checked 2026-10-10 UTC. Source and installed artifacts were tested separately.

| Native platform | Python | Source suite | Clean wheel, resources and Empire attachment |
| --- | --- | --- | --- |
| Windows | 3.13.3 | 114 tests, 4 skips | PASS |
| Linux x86_64 | 3.13.5 | 114 tests, 1 skip | PASS |
| macOS arm64 | 3.13.7 | 114 tests, 1 skip | PASS |

The source-suite wheel test skips when no wheel is installed; a separate
installed-wheel gate passed on every platform. Three Windows symlink tests
skip where the account cannot create symlinks; the POSIX runs execute them.
These are environment limits, not silently counted passes.

- The suite covers endpoint and query restrictions, redirects, HTTPS origins,
  credential and error handling, output redaction, incomplete records,
  target identity, deployment windows, report preservation and resource
  integrity. Malformed or partial data is not reported as complete success.
- Each platform built a wheel and source distribution. A fresh wheel install
  outside the checkout passed version, offline doctor, resource discovery,
  required documentation and local-link checks. All 19 declared knowledge
  files passed SHA-256 verification.
- The installed library was tested against the released `legends-empire`
  0.3.1 engine: preview without writes, fresh attachment, repeat no-op,
  upstream update preserving the user's index and private notes, and refusal
  of edited reference files before mutation. Tests used synthetic vaults.
- GitHub Actions runs six core jobs across Windows, macOS and Linux with
  Python 3.11 and 3.14, plus three native Empire attachment jobs with Python
  3.11. Consult the checks on the exact release commit for their result.
- Source and distribution checks cover required files, Markdown links,
  artifact notices, image metadata and known private-residue patterns.
- Authorized live reads from an installed Windows wheel passed against
  Coolify 4.3.14: authenticated doctor, inventory, resource status,
  environment names, advisory plan, queued/running deployments, application
  deployment history, individual deployment metadata and two databases'
  backup schedules. Both selected schedules were empty. No provider
  mutations occurred; live records remain private.

Live API use was tested from Windows, not independently repeated from macOS
and Linux. Official-source review and unit tests do not prove compatibility
with every Coolify version. Environment values and deployment logs are excluded.
Collected state does not certify application health, completed backups,
restorability or deployment execution.

The core CLI requires Python 3.11+. Optional Empire attachment requires
Python 3.11+; native Windows writes require local fixed NTFS and the released
Empire backend's security conditions. Power-loss durability is not claimed
equivalent to POSIX directory flushing. Installation never writes to a vault.

## 0.1.0

Checked 2026-09-26.

- Windows, Python 3.11: 19 offline tests passed, covering endpoint restrictions, redirects, HTTPS origins, redaction, error handling, malformed records, target identity, partial collections and report preservation.
- Public-source checks passed: required files, Markdown links, naming punctuation and private-residue patterns.
- An independent code review found a malformed-resource response that could be treated as a successful plan. The release now requires a matching target UUID; regression tests cover incomplete list rows and mismatched plans.
- Authorized read-only calls against Coolify 4.3.14 completed: authenticated doctor, inventory, resource status, application environment names, advisory plan and database backup schedules. Both empty and nonempty backup schedules were observed. No infrastructure changes were performed.
- All live evidence remains private. These results do not certify application health, successful backups, restore capability, write operations or every Coolify version.

Cross-platform installation and offline checks run in the repository's GitHub Actions matrix. Consult the checks attached to the release commit for their result. Only Windows live API use was tested for this first release.

The [source ledger](../references/sources.md) separately records the researched knowledge baseline. This release does not claim a Brainstein certification or a completed disaster recovery drill.
