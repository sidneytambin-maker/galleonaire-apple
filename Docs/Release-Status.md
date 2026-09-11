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
- Cloud run 34591800746 passed all 25 core tests and five of seven iPhone UI tests, including the home accessibility audit and large-text test.
- The same run produced an unsigned release archive with the correct embedded Watch app, identifiers, versions and resources.
- Run 34593755546 passed all seven iPhone UI tests, including Settings, cancellation, resume, answer states, large text and the home accessibility audit.
- Signing Verification run 34594713210 produced a distribution-signed 0.1.0 (1) IPA. Both embedded profiles and iPhone/Watch metadata passed inspection. The downloaded IPA SHA256 is 345a28f076168acab09aa03484fd830ce1e9f1acf6cce2455c6c51e85b7996f6.
- All 17 local identity, package and actual-media regression tests pass. Icons are opaque 1024-pixel RGB; eleven event recordings are distinct, non-silent and unclipped.
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

- Both Watch tests in run 34593755546 still failed later navigation. Recordings show fast swipes skipping rows; the Free Pass row was absent from the lazy list before scrolling. Small Digital Crown steps now replace the fling gestures, with a targeted Watch rerun pending.
- The user confirms App Store Connect is signed in on Google Chrome. The computer-control tool reports an Escape interruption before reading the page, so that session has not been reverified or operated.
- No Galleonaire App Store Connect app record, uploaded build or TestFlight release exists yet.
- Physical-device gameplay, VoiceOver and audio checks remain outstanding.
- External beta configuration, review submission and public link remain outstanding.

Use Google Chrome only for browser interaction and authentication. Do not reopen the in-app browser.
Do not describe this sprint as complete until the release and verification work is actually done.
