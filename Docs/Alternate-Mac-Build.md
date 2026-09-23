# Alternate Mac validation route

Build 16 used the authorised public GitHub repository and free standard Mac runners
successfully. Codemagic was not needed or connected. The configuration below remains
an unused alternative. See Release-Status.md for the live release.

The manual `native-validation` workflow in root `codemagic.yaml` runs the existing
question validation, Python tests, shared Swift tests, iPhone and Watch UI tests,
and unsigned release archive. It preserves the exact source revision, logs,
simulator evidence and archive in `native-validation.tar.gz`, including diagnostics
when native validation fails. A success marker is emitted only after all stages pass.

This workflow has not yet run. It requires the owner's Codemagic account and an
authorised connection to this private GitHub repository. It has no automatic
triggers, publishing settings or Apple signing credentials. Use the personal free
Mac allowance if available; do not enable paid usage without explicit approval.

After connection, select main and the Galleonaire iPhone and Watch validation workflow.
Verify the service's completed build status and source revision independently before
using its artifact. Inspect every native test result and simulator evidence. The
archive must contain the changed native implementation and both 600-question banks.

Local signing/upload can follow the build 13 approach, but its existing validator
currently requires GitHub-native evidence and the previous Swift test count. Add a
separately verified Codemagic evidence path before use; do not bypass that validator
or claim the new workflow satisfies it unchanged. Preserve all signature, archive,
source identity and Apple processing checks. No update has been uploaded by this setup.

References:
- https://docs.codemagic.io/billing/pricing/
- https://docs.codemagic.io/yaml-basic-configuration/yaml-getting-started/
- https://docs.codemagic.io/yaml-quick-start/building-a-native-ios-app/

Fresh GitHub retry 35889456262 was also refused before any native steps on
23 September 2026, with the same billing/spending annotation. The Apple account
returned zero Xcode Cloud products; GitHub returned no repository webhooks or
self-hosted runners. These checks found no existing alternate Mac connection.
