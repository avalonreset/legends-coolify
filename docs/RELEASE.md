# Release procedure

This module ships a read-only Coolify CLI and reusable operational knowledge.
A public tag alone does not complete a release. Use the central
[module release contract](https://github.com/avalonreset/cto-legends/blob/main/docs/MODULE-RELEASE.md)
and keep an evidence receipt outside the distributed source.

## Product and evidence

1. Inspect the actual previous release and current official Coolify sources.
   Explain the implemented value, changed behavior and unsupported work.
2. Review the source ledger, local links, credential handling and public/private
   ownership. Never copy a private instance inventory or operational report
   into this repository.
3. Run all offline tests and `python scripts/check_release.py`. Test malformed
   and partial provider responses, target identity, output redaction and report
   preservation. Keep the fixed read-only endpoint boundary.
4. Build the wheel and source distribution. Inspect their contents and install
   the wheel into a clean environment outside the checkout. Verify offline
   doctor and the packaged recipe and knowledge paths.
5. Test the declared Windows, macOS and Linux environments, including native
   Windows separately from WSL. Run the supported Python CI matrix on the exact
   release commit. Record the interpreter and platform for fleet checks.
6. Use an authorized Coolify instance for representative live reads. Record its
   version and command outcomes privately; publish only a sanitized summary.
   Provider-reported status is not independently verified service health,
   backup integrity or a successful restore.
7. Verify the packaged knowledge library against the released Empire engine:
   preview, attach, repeat, upstream update, preservation of user notes and
   refusal to overwrite modified references. No vault is changed during install.

## Presentation and publication

1. Resolve `legends-github` through the router. Run the appropriate readiness,
   audit, researched SEO, metadata, README, legal and release workflows.
   Apply useful findings rather than optimizing a checklist score.
2. Verify attribution and license notices, generic onboarding, banner and
   social artwork. Upload the social card through a supported authenticated
   browser route; verify the saved setting and the image GitHub serves.
3. Update changelog, release notes and validation evidence. Build final artifacts
   after all included files are frozen. Record SHA-256 checksums and scan both
   source and distribution for private residue.
4. Push and wait for the exact-commit CI result before creating a unique
   version tag and public release. Attach the tested artifacts and checksums.
   Never replace a released version with different bytes.
5. Download the immutable codeload archive and compute the checksum the manager
   will use. Update the `cto-legends` catalog version, module identity,
   discovery, recipe paths and probes. Keep the single router skill unchanged.
6. Verify fresh public installation and upgrade from the prior version,
   doctor, run, instruction handoff, packaged knowledge and outcome routing.
   Publish the catalog and verify the normal remote sync path.
7. Add or update the publisher's ecosystem profile directory. Preserve its
   approved layout and generator behavior; verify the module link in the live
   README. Catalog admission and profile inclusion are separate checks.
8. Close the receipt with exact public URLs, versions, test results, live
   evidence, costs and explicit remaining limitations.

The knowledge library is optional: read it as Markdown or attach it with
`legends-empire`. Coolify, a cloud provider account and Empire are not needed
for offline readiness. Live reads require the user's own configured instance.
Provider server operations belong to `legends-hetzner`; this module does not
install Coolify, deploy applications or mutate infrastructure.
