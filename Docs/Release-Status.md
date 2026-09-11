# Galleonaire Release Status

Last updated: 11 September 2026.

## Verified

- This is a personal project named Galleonaire, with no company attribution.
- Personal iPhone and Watch identifiers are registered with Apple.
- The private repository is sidneytambin-maker/galleonaire-apple.
- The testflight environment permits only the main branch, verified through GitHub's API.
- Seven signing/upload values are stored as encrypted secrets in that environment, after the user's specific approval. No credentials are committed to source code.
- Native source and release workflow revision 74d231e has been published to the private repository.
- The original 300-question collection passes migration validation.
- All 25 shared Swift game/settings tests passed in cloud run 34585492531.
- Cloud run 34591800746 passed all 25 core tests and five of seven iPhone UI tests, including the home accessibility audit and large-text test.
- The same run produced an unsigned release archive with the correct embedded Watch app, identifiers, versions and resources.
- Run 34593755546 passed all seven iPhone UI tests, including Settings, cancellation, resume, answer states, large text and the home accessibility audit.
- Signing Verification run 34594713210 produced a distribution-signed 0.1.0 (1) IPA. Both embedded profiles and iPhone/Watch metadata passed inspection. The downloaded IPA SHA256 is 345a28f076168acab09aa03484fd830ce1e9f1acf6cce2455c6c51e85b7996f6.
- Full TestFlight Release run 34597392997 passed all 25 shared Swift tests, all seven iPhone UI tests, both Watch UI tests, archive validation and distribution signing on revision 74d231e.
- That run produced the current distribution-signed 0.1.0 (2) IPA, with verified embedded Watch app and distribution profiles. It was intentionally run with upload=false because the Apple app record does not yet exist.
- The downloaded build 2 IPA SHA256 is 0c69efb4183f88e31f121cc0864fb3b54cca85b55a3c063753da9030b73c5939.
- All 22 local identity, package, beta metadata and actual-media regression tests pass. Icons are opaque 1024-pixel RGB; eleven event recordings are distinct, non-silent and unclipped.
- The latest large-text iPhone screenshot confirms separate answer-letter and answer-text columns. Native layout assertions pass at the largest accessibility text size.
- Watch tests successfully start an independent game, select and lock an answer, reach a result, activate Free Pass, resume and open Settings. Screenshots and accessibility trees are retained alongside the test results.
- Release scripts and YAML configuration pass local syntax checks.

## Implemented and Cloud-Verified

- Answer-button accessibility changes, larger Settings touch target and stable identifiers.
- More detailed accessibility-tree and screenshot evidence from both UI test suites.
- Selection of stable Xcode 26 or later, required for current Apple uploads.
- Separate iPhone, Watch and archive checks, including when another UI suite fails.
- A release workflow gated on successful native validation.
- Package checks for the embedded Watch app, matching builds, distribution profiles and absence of signing-key files.
- Ephemeral cloud signing setup and cleanup, without saving new signing files locally.

## Incomplete

- Earlier Watch test helpers failed because fast swipes overshot controls, lazy list cells were initially absent, and simulated Crown input did not advance the scroll view in run 34595660707. The successful tests now use the full content window, bounded touch drags, and a hold to stop momentum; each target position is logged.
- The user confirms App Store Connect is signed in on Google Chrome. The computer-control tool reports an Escape interruption before reading the page, so that session has not been reverified or operated.
- The Apple API still returns no Galleonaire App Store Connect app record. No build has been uploaded to Apple and no TestFlight release exists yet. The successful workflow step is named "Sign, inspect and upload", but its upload=false input and the package report explicitly confirm uploaded=false.
- Physical-device gameplay, VoiceOver and audio checks remain outstanding.
- External beta configuration, review submission and public link remain outstanding.

Use Google Chrome only for browser interaction and authentication. Do not reopen the in-app browser.
Do not describe this sprint as complete until the release and verification work is actually done.

## Resume Point

- Current IPA: Artifacts/Run-34597392997/galleonaire-testflight-package-2/TestFlight/Galleonaire.ipa.
- Native evidence: Artifacts/Run-34597392997/galleonaire-release-tests-2.
- The user has repeatedly authorized the app's development, private source publication, approved encrypted signing setup and TestFlight release. This is not awaiting another permission or sign-in.
- Chrome control again returned an Escape interruption before listing windows after the user's latest explicit continuation. The user uses Escape for NVDA and has not intentionally asked to stop. Do not bypass the tool's interruption or use the inaccessible in-app browser.
- Apple requires creation of the new app record on its website; its documented Apps REST API cannot create it. Use name Galleonaire, iOS platform, en-GB, bundle com.sidneytambin.galleonaire, SKU GALLEONAIRE-IOS-2026. Do not alter Court Story.
- Once that record exists, run TestFlight Release with upload=true (the next release workflow build number is 3), wait for Apple processing, run Scripts/beta_metadata.py with a successful full release run and the existing protected review-contact file, then assign the exact build, owner tester and external group, submit beta review and enable the shareable link when Apple permits it.
- Scripts/beta_metadata.py has five passing local tests but has not been executed against Apple for this app yet. Review submission, tester assignment and link activation are still live tasks, not completed operations.
- Physical VoiceOver, audio mixing, haptics and paired-device settings delivery remain device-test-required. Simulator results are not physical-device evidence.

Apple references: https://developer.apple.com/documentation/appstoreconnectapi/apps and https://developer.apple.com/help/app-store-connect/create-an-app-record/add-a-new-app.
