# Third-Party Notices

`legends-coolify` ships with zero third-party runtime dependencies in `pyproject.toml` and uses the Python 3.11+ standard library only (`urllib.request`, `ssl`, `json`, `argparse`, `hashlib`, `pathlib`).

## External Upstream APIs and References

- **Coolify API (`/api/v1`) and Documentation:** `legends-coolify` communicates with user-operated Coolify instances over verified HTTPS and cites official Coolify documentation (`https://coolify.io/docs`). No Coolify source code or SDK is bundled.
- **CTO Legends Central Router (`skills/cto-legends/SKILL.md`):** Vendored byte-for-byte from `avalonreset/cto-legends` under the MIT License.
