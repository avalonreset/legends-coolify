<a name="legends-coolify"></a>

# ![legends-coolify](assets/banner.webp)

[![release](https://img.shields.io/github/v/release/avalonreset/legends-coolify?label=release&sort=date&style=flat-square&labelColor=000000&color=ff0000)](https://github.com/avalonreset/legends-coolify/releases/latest)
[![checks](https://img.shields.io/github/actions/workflow/status/avalonreset/legends-coolify/checks.yml?branch=main&label=checks&style=flat-square&labelColor=000000)](https://github.com/avalonreset/legends-coolify/actions/workflows/checks.yml)
[![license](https://img.shields.io/github/license/avalonreset/legends-coolify?label=license&style=flat-square&labelColor=000000&color=666666)](LICENSE)

A read-only Coolify CLI and source-cited operations library for AI agents.
Inspect your self-hosted applications, review environment-variable metadata and
backup schedules, inspect deployment history, and carry the same runbooks into
the next session.

Start with **[the knowledge index](wiki/index.md)** or install through
[cto-legends](https://github.com/avalonreset/cto-legends). The library covers
inventory, health, environment review, backups, rollback planning and migrations.
It works as plain Markdown, an Obsidian vault, or an optional `legends-empire`
knowledge shelf.

## What it adds

- Lists applications, databases, services, servers and projects with selected metadata.
- Reports container state without mistaking it for application health.
- Lists application environment variable names and flags; never exports their values.
- Inspects database backup schedules, while keeping backup success and restore verification separate.
- Reads queued/running deployments, bounded application history and a selected
  deployment's metadata.
- Prepares an advisory deployment checklist for a selected application.
- Gives agents a source-cited knowledge library with an index, dated references
  and reusable private-record templates.

### Why use this alongside Coolify?

[Coolify](https://coolify.io/) runs the application platform.
Its [official CLI](https://github.com/coollabsio/coolify-cli), API and UI provide
the underlying controls. `legends-coolify` gives an agent a smaller, repeatable
inspection procedure: check access, collect selected fields, report incomplete
collections, and consult the relevant runbook before proposing an operation.

This early release only inspects. It does not deploy, start, stop, restart,
trigger backups, restore, edit DNS or change configuration. Its deployment plan
is an advisory checklist, not an executable deployment. Use Coolify's official
tools for an authorized change. This project is independently maintained and
is not an official Coolify integration.

## Install with your agent

The shared `cto-legends` skill discovers the module and loads its
[agent recipe](docs/AGENT-RECIPE.md) on demand. It is the only registered skill;
no additional module skill, MCP server or model subscription is required by this package.

```sh
cto-legends sync --apply
cto-legends install legends-coolify --apply
cto-legends handoff legends-coolify
cto-legends run legends-coolify -- doctor
```

For an existing managed installation, use `cto-legends update legends-coolify --apply`.
Omit `--apply` to preview installation or updates. Catalog sync makes the
module discoverable; installation remains a separate choice.

### Standalone install

Python 3.10 or newer on Windows, macOS or Linux. The CLI uses the Python standard
library and has no runtime dependencies. Use `python3` where that is your
Python command. See [validation](docs/VALIDATION.md) for tested versions and limits.

```sh
git clone --branch v0.2.0 https://github.com/avalonreset/legends-coolify.git
cd legends-coolify
python -m pip install .
legends-coolify doctor
legends-coolify resources
```

Source and wheel installations include the knowledge library. Read it without
credentials or open the source checkout in Obsidian. Installation does not
connect to Coolify or modify an existing vault. `resources` reports absolute
`root`, `recipe`, `pack_dir`, `pack_manifest` and `pack_files` paths as JSON.
Its `source` field distinguishes packaged files from a source checkout, and
`complete` confirms the recipe and every manifest-pinned reference passed
integrity checks. Missing or incomplete resources cause a nonzero exit.
Through the router, run `cto-legends run legends-coolify -- resources`.

## Quick start: inspect your Coolify instance

Set `COOLIFY_BASE_URL` to the HTTPS **origin**, such as `https://coolify.example.com`, and `COOLIFY_API_TOKEN` to a token with `read` permission. Load the token from your own secret manager into the environment. Do not put a real token in chat, shell history or a repository.

The client requires verified HTTPS, refuses redirects and ignores ambient proxy variables. Use a direct reachable instance or an operator-managed tunnel with a valid HTTPS origin. No default house server, local credential file discovery or insecure TLS switch is included.

```sh
legends-coolify doctor --live
legends-coolify inventory
legends-coolify health
legends-coolify env --uuid YOUR_APPLICATION_UUID
legends-coolify backups --uuid YOUR_DATABASE_UUID
legends-coolify deployments
legends-coolify deployments --uuid YOUR_APPLICATION_UUID --limit 10 --skip 0
legends-coolify deployments --deployment-uuid YOUR_DEPLOYMENT_UUID
legends-coolify plan --uuid YOUR_APPLICATION_UUID
```

`deployments` without a target reads currently queued or running deployments.
Use `--uuid` for an application's retained history: the response describes the
requested window and reports whether more entries remain. `--limit` accepts
1-50 entries; increase `--skip` to read another window. `--deployment-uuid`
reads one exact deployment. None of these commands starts a deployment.

Commands emit JSON. Inspection commands accept
`--out /path/to/private/new-report.json` to create a report instead of printing
it; `resources` prints to standard output. The parent directory must exist;
existing files are never overwritten. Reports still contain operational names
and UUIDs. Keep them in your private workspace, outside this public vault and
any managed installation.

`doctor` is offline installation proof. `doctor --live` verifies instance health and authenticated application listing. `health` collects resource status; a successful collection does not prove the application works. Exit 0 means the requested collection completed, 1 means error or partial collection, and 2 means invalid CLI arguments. Missing endpoint access is reported, never silently counted as zero resources.

## Where it fits in the Legends ecosystem

| Component | Responsibility |
| --- | --- |
| [legends-hetzner](https://github.com/avalonreset/legends-hetzner) | Inspect and provision Hetzner Cloud servers through reviewed provider workflows. |
| [Coolify](https://coolify.io/) | Build and run applications, services and databases on your chosen servers. |
| `legends-coolify` | Inspect that platform and guide your agent through source-cited operational procedures. |
| [legends-empire](https://github.com/avalonreset/legends-empire) | Keep reusable module references alongside your private project notes and decisions. |
| [cto-legends](https://github.com/avalonreset/cto-legends) | Discover, install, update and hand off the appropriate module through one skill. |

Hetzner is optional: Coolify can run on other supported infrastructure. This
module does not install Coolify or require a `legends-empire` vault.

For optional `legends-empire` attachment, follow [the knowledge guide](docs/KNOWLEDGE.md)
and [the attachment procedure](docs/KNOWLEDGE-PACK.md). The self-contained reference
pack has its own version and `knowledge/coolify/pack.json` manifest. Managed references
remain separate from your private inventory, decisions and receipts. Attachment
is explicit; updates preserve user notes and refuse conflicting reference edits.
`legends-empire` 0.3.1+ requires Python 3.11+ for attachment; native Windows writes require
local fixed NTFS. The CLI itself retains its Python 3.10+ requirement.

## Architecture and project layout

| Location | Purpose |
|---|---|
| `wiki/` | Reusable source-cited knowledge, runbooks and navigation |
| `references/` | Dated source evidence and claim coverage |
| `templates/` | Starting points for private operational records |
| `knowledge/coolify/` | Versioned, self-contained `legends-empire` reference pack |
| `legends_coolify/` | Portable read-only CLI |
| `tests/` | Transport, output and knowledge checks |
| `skills/cto-legends/SKILL.md` | Unmodified central router recipe |

Private infrastructure and the earlier house PowerShell tools are not distributed here. Their operational lessons inform this module, but there is no automatic migration of credentials or production fixtures.

## FAQ

**Does `legends-coolify` deploy, restart, or mutate Coolify resources?**
No. This release is strictly read-only. It inspects applications, databases, services, servers, environment variable metadata (never secret values), backup schedules, and deployment history, and generates advisory deployment checklists.

**Why does `legends-coolify` refuse HTTP or self-signed redirects?**
The transport requires verified HTTPS origins, refuses redirects, and ignores ambient proxy variables so that API tokens are never forwarded over unverified links.

## Contribute

Read [the contribution guide](CONTRIBUTING.md), [AGENTS.md](AGENTS.md),
[the security policy](SECURITY.md) and [the release checklist](docs/RELEASE.md).
Check official sources when changing domain guidance. Pair recurring operational
failures with a corrected runbook and, where executable, a regression test.

```sh
python -m unittest discover -s tests -v
python scripts/check_release.py
python -m legends_coolify doctor
```

MIT licensed. Documentation links to upstream sources; no Coolify source code is
bundled. See [attribution](NOTICE.md) and [support](SUPPORT.md).
