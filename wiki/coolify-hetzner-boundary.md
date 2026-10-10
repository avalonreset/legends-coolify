# Coolify and Hetzner boundary

Coolify on Hetzner Cloud is an optional application layer above an ordinary server. This module inspects the Coolify layer through its API; it never provisions servers, manages SSH keys, or reads Coolify state through the Hetzner API. The sibling `legends-hetzner` module owns the server layer and documents the same boundary from its side.

## What the Hetzner Coolify app is

- Hetzner maintains a ready-to-deploy Coolify app image chosen at server creation instead of a plain OS image. Install paths are the Cloud Console, the Cloud API, or `hcloud server create` with `--image coolify`. [App README](https://github.com/hetznercloud/apps/blob/main/apps/hetzner/coolify/README.md)
- Image contents per the README: Ubuntu 24.04 with Docker, and Coolify itself as containers.
- Coolify is preinstalled but not activated until the first server login over SSH or the mailed root password; activation prints the administration interface URL.
- Hetzner builds app images with Packer and cloud-init, keeps officially maintained apps under `apps/hetzner`, and mirrors the build files in the public apps repository. App issues go to that repository; other cloud issues go through a normal support ticket. [Apps repository](https://github.com/hetznercloud/apps)

## Ownership boundary

| Layer | Owner | Notes |
| --- | --- | --- |
| App image build and publish | Hetzner | Packer and cloud-init build; see the apps repository. Image faults are Hetzner-side. |
| Server lifecycle, keys, backups, snapshots | Server owner plus `legends-hetzner` | Planned creates, read-only checks, private server records. |
| Coolify behavior, projects, env vars, domains, in-app backups | Coolify upstream and the server owner | Docs at `https://coolify.io/docs/`. Never in server-module scope. |
| Credentials and app data on the server | Server owner | Keep in owner records, never in this vault or pack. |

This module bundles no Coolify software and no Hetzner tooling. Nothing in it reads or writes server state or Coolify state beyond its documented read-only API calls.

## Suggested practice

1. Treat the server and the PaaS as separate evidence layers: confirm the server is reachable and the Coolify control plane responds before interpreting any application status. See [inventory and health](inventory-and-health.md).
2. Record the app choice, activation URL owner, and Coolify admin owner in the private server record, not in reusable notes.
3. Keep Coolify upgrades, project config, and domain wiring in Coolify itself plus owner notes. A server rebuild or restore follows the server owner's recovery plan; Coolify instance recovery follows [backups and restore](backups-and-restore.md).
4. Route problems: Hetzner app-image build or provisioning faults to Hetzner; application deployment or runtime faults to Coolify docs and community plus the application owner; wrapper faults to the module issue tracker with a redacted receipt.

See [sources S17-S18](../references/sources.md).
