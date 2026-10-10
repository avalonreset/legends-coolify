# Contributing

Start with [AGENTS.md](AGENTS.md), [the agent recipe](docs/AGENT-RECIPE.md)
and [the knowledge index](wiki/index.md). Keep changes focused on repeatable
read-only Coolify checks and accurate, source-cited operating guidance.

Use Python 3.10+ and a local checkout:

```sh
python -m pip install .
python -m unittest discover -s tests -v
python scripts/check_release.py
python -m legends_coolify doctor
```

Use `python3` instead where required. Run tests without credentials first.
Live checks require a separately authorized instance and a read-only token;
never include real responses, inventory or credentials in fixtures.

When changing the client, test denied endpoints, malformed responses and partial
collections as well as successful reads. Preserve the distinction between
container status, application health, backup configuration and proven recovery.
Do not add write endpoints as an incidental change.

When changing knowledge, cite the official source and review date in
[the source ledger](references/sources.md). Keep links usable both in the
source checkout and the packaged library. Update knowledge hashes when managed
references change, following [the knowledge guide](docs/KNOWLEDGE.md).

In a pull request, explain the user-visible problem, the resulting behavior,
the checks run and any untested platforms or live behavior. Screenshots and logs
must be sanitized. See [SECURITY.md](SECURITY.md) for vulnerability reports.
