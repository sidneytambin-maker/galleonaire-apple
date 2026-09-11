# Galleonaire Release Status

Last updated: 11 September 2026.

## Verified

- This is a personal project named Galleonaire, with no company attribution.
- Personal iPhone and Watch identifiers are registered with Apple.
- The private repository is sidneytambin-maker/galleonaire-apple.
- The testflight environment permits only the main branch, verified through GitHub's API.
- Seven signing/upload values are stored as encrypted secrets in that environment, after the user's specific approval. No credentials are committed to source code.
- Source and release workflow revision e25bc7c has been published to the private repository.
- The original 300-question collection passes migration validation.
- All 25 shared Swift game/settings tests passed in cloud run 34585492531.
- All 14 local personal-identity and synthetic-package regression tests pass.
- Release scripts and YAML configuration pass local syntax checks.

## Implemented, Still Awaiting Native Verification

- Answer-button accessibility changes, larger Settings touch target and stable identifiers.
- More detailed accessibility-tree and screenshot evidence from both UI test suites.
- Selection of stable Xcode 26 or later, required for current Apple uploads.
- Separate iPhone, Watch and archive checks, including when another UI suite fails.
- A release workflow gated on successful native validation.
- Package checks for the embedded Watch app, matching builds, distribution profiles and absence of signing-key files.
- Ephemeral cloud signing setup and cleanup, without saving new signing files locally.

## Incomplete

- The first iPhone UI run failed seven tests. Cloud run 34591800746 is testing the fixes on both platforms.
- Watch UI validation, successful release archive and inspection of an actual signed IPA remain outstanding.
- The Chrome Apple session requires fresh sign-in. The apparent signed-in page was stale; navigation confirmed expiry.
- No Galleonaire App Store Connect app record, uploaded build or TestFlight release exists yet.
- Physical-device gameplay, VoiceOver and audio checks remain outstanding.
- External beta configuration, review submission and public link remain outstanding.

Use Google Chrome only for browser interaction and authentication. Do not reopen the in-app browser.
Do not describe this sprint as complete until the release and verification work is actually done.
