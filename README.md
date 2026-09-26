# legends-coolify

A Coolify knowledge vault and read-only operational toolkit for you and your agent.

Start with **[the knowledge vault](wiki/index.md)**. It connects current official sources to practical runbooks for inventory, health, environment review, backups, rollback planning and migrations. The CLI provides repeatable evidence without deploying or modifying your infrastructure.

## What 0.1.0 does

- Lists applications, databases, services, servers and projects with selected metadata.
- Reports container state without mistaking it for application health.
- Lists application environment variable names and flags; never exports their values.
- Inspects database backup schedules, while keeping backup success and restore verification separate.
- Prepares an advisory deployment checklist for a selected application.
- Gives agents a maintained, source-cited knowledge vault rather than making every session start from scratch.

This is an early read-only release. It does not deploy, start, stop, restart, trigger backups, restore, edit DNS or change configuration. It is independently maintained and is not an official Coolify integration. Use Coolify's own CLI, API or UI when an authorized task requires execution.

## Install

Python 3.10 or newer. No runtime dependencies, MCP server or agent subscription is required by this package.

```sh
git clone https://github.com/avalonreset/legends-coolify.git
cd legends-coolify
python -m pip install .
legends-coolify doctor
```

The repository/source distribution contains the vault. A wheel installs the CLI; keep a source checkout or use the CTO managed source for the knowledge files. Open the repository folder in Obsidian if desired; all notes also work as plain Markdown.

## Connect your instance

Set `COOLIFY_BASE_URL` to the HTTPS **origin**, such as `https://coolify.example.com`, and `COOLIFY_API_TOKEN` to a token with `read` permission. Load the token from your own secret manager into the environment. Do not put a real token in chat, shell history or a repository.

The client requires verified HTTPS, refuses redirects and ignores ambient proxy variables. Use a direct reachable instance or an operator-managed tunnel with a valid HTTPS origin. No default house server, local credential file discovery or insecure TLS switch is included.

```sh
legends-coolify doctor --live
legends-coolify inventory
legends-coolify health
legends-coolify env --uuid YOUR_APPLICATION_UUID
legends-coolify backups --uuid YOUR_DATABASE_UUID
legends-coolify plan --uuid YOUR_APPLICATION_UUID
```

All commands emit JSON. Add `--out /path/to/private/new-report.json` to create a report instead of printing it. The parent directory must exist; existing files are never overwritten. Reports still contain operational names and UUIDs. Keep them in your private workspace, outside this public vault and any managed installation.

`doctor` is offline installation proof. `doctor --live` verifies instance health and authenticated application listing. `health` collects resource status; a successful collection does not prove the application works. Exit 0 means the requested collection completed, 1 means error or partial collection, and 2 means invalid CLI arguments. Missing endpoint access is reported, never silently counted as zero resources.

## CTO ecosystem

The central `cto-legends` skill loads this module's [agent recipe](docs/AGENT-RECIPE.md) on demand. Do not register another module skill.

After this release is admitted to the public catalog:

```sh
cto-legends sync
cto-legends sync --apply
cto-legends install legends-coolify
cto-legends install legends-coolify --apply
cto-legends handoff legends-coolify
cto-legends run legends-coolify -- doctor
```

Catalog admission requires a published immutable release, archive checksum and verified install. Publishing a GitHub repository alone does not enable discovery. A catalog sync adds discovery; installation remains a separate explicit choice. No manager or router skill release is needed for this module's existing Python recipe.

## Project organization

| Location | Purpose |
|---|---|
| `wiki/` | Reusable source-cited knowledge, runbooks and navigation |
| `references/` | Dated source evidence and claim coverage |
| `templates/` | Starting points for private operational records |
| `legends_coolify/` | Portable read-only CLI |
| `tests/` | Transport, output and knowledge checks |
| `skills/cto-legends/SKILL.md` | Unmodified central router recipe |

Private infrastructure and the earlier house PowerShell tools are not distributed here. Their operational lessons inform this module, but there is no automatic migration of credentials or production fixtures.

## Contribute

Read [AGENTS.md](AGENTS.md), [the security policy](SECURITY.md) and [the release checklist](docs/RELEASE.md). Check official sources when changing domain guidance. Pair recurring operational failures with a corrected runbook and, where executable, a regression test.

```sh
python -m unittest discover -s tests -v
python scripts/check_release.py
python -m legends_coolify doctor
```

MIT licensed. Documentation links to upstream sources; no Coolify source code is bundled.
