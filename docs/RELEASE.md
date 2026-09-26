# Early release checklist

Target: 0.1.0, a useful read-only module with a reusable knowledge vault. No claim of comprehensive Coolify coverage, certified Brainstein maturity, production deployment automation or tested disaster recovery.

1. Review official source dates, links and claim coverage; check knowledge links and public/private separation.
2. Run all offline tests and `python scripts/check_release.py`.
3. Build wheel and source distribution. Install the wheel into a clean environment; run offline doctor without credentials.
4. Verify read-only doctor and chosen commands against an authorized Coolify instance. Keep its private evidence outside the repo. Record version and bounded test results only.
5. Run Windows/Linux/macOS CI for portability. Identify untested live-platform claims explicitly.
6. Inspect source archive contents and checksums. Release only intended public files, never the house predecessor folder.
7. Publish tag and release. Record immutable commit and SHA-256 of its codeload ZIP.
8. Add the complete module entry to the public `cto-legends` catalog and bump its catalog version. Do not change manager version or frozen skill text.
9. Test catalog contracts and a fresh install from the release archive, then verify discovery, handoff, doctor and run.
10. Publish the catalog update. Prove remote sync, install and handoff from a fresh manager home.

The canonical source archive includes the knowledge vault and CLI; the wheel installs the CLI. A public catalog entry is reviewed admission, not automatic repository discovery. Consumers sync the catalog before installing a newly admitted module.
