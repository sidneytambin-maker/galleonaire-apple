# Galleonaire Release Status

Last verified: 12 September 2026, 23:53 UTC (13 September, 00:53 BST).

## Current Release

- Galleonaire 0.1.0 (13) is APPROVED and IN_BETA_TESTING for internal and external testers.
- App Store Connect app: 6811170867; bundle: com.sidneytambin.galleonaire.
- Apple build and completed upload: ee46cdc3-9bed-4ed1-a02f-36b876160d9d.
- Processing is VALID, unexpired, with usesNonExemptEncryption false. The completed upload has no errors or warnings.
- Owner Testing and Community Beta contain the exact build 13, verified by independent API readback. Automatic tester notification is enabled.
- The existing public invitation link remains enabled with an enforced limit of 100 testers. Retrieve its URL from the existing Community Beta group; no new audience or invitation was created.
- Updated beta description, review notes and What to Test notes were saved and read back. No public App Store release was submitted.
- This remains a personal project. Court Story/Tennis Tracker and the original handheld application were not modified.

## Shipped Changes

- Correct answers atomically advance to the next question, without a Next button, confirmation or timer. A stale answer tap cannot score the next question.
- The new question's combined VoiceOver label includes the previous correct answer, explanation and prize before the next question. Focus is requested on the new question; real-device speech timing still needs user testing.
- Wrong answers end the game immediately. The result distinguishes the question/prize reached from guaranteed winnings kept. Main Menu and Play Again remain available after losing, winning or walking away.
- More dramatic original 2.8-second loss sound and 6.6-second million-galleon celebration. Existing individual previews and independent 0-100 percent music/effects controls remain.
- Original magical-library/open-book artwork replaces the decorative central circle. Native text scaling, separate answer columns, contrast, prize progress and VoiceOver semantics are preserved.
- 450 shared questions, exactly 30 at every prize level: 150 additions, ten per level. Twenty-three older questions were replaced and fifteen clarified following duplicate/ambiguity review.
- Every addition and replacement has an underlying fact identifier and traceable primary-source note. See Question-Review-450.md for the review method and limits; automated uniqueness checks are not a claim of infallible fact checking.
- Fresh launch still opens the menu without restoring a partial game. Highest prize, settings and recent-question history are retained.

## Test and Package Evidence

- Private repository: sidneytambin-maker/galleonaire-apple, main.
- Native source: f9303ae41a73bc663f2ce254e94f3863a4489880.
- Run 34723039177 validation job passed: 38 shared Swift tests, 13 iPhone UI tests, six Watch UI tests and 45 Python tests. No skipped tests. Release archive succeeded.
- Later release-tooling changes have 57 passing local regression tests, including a run without third-party Python packages. Native app code/content is unchanged from the tested revision.
- Native tests cover automatic progression through all fifteen levels on both devices, million-prize and loss/menu flows, lifelines, fresh-launch reset, settings and accessibility layouts.
- Native screenshots of home, automatic progression, victory and largest-text layouts were inspected. Simulator devices were iPhone 17 Pro Max and Watch Ultra 3, not the owner's physical devices.
- The cloud release job could not start because of a GitHub billing/spending restriction. It is not reported as a successful full cloud release. No billing setting was changed and no private source or credentials were made public.
- The exact native-tested archive was signed locally with rcodesign 0.29.0, correct active App Store profiles and the existing distribution identity, then uploaded using Apple's buildUploads API. See Local-Release.md.
- Accepted IPA: Artifacts/LocalSigned13RC2/Galleonaire.ipa.
- SHA256: ee5c205f9728d35b3fb345fafe239ac846991b7e7fbbc01840437ec5a229a22b.
- Both apps have version 0.1.0/build 13. Watch remains at Payload/Galleonaire.app/Watch/GalleonaireWatch.app, with the correct companion ID.
- Independently checked ZIP integrity, native sections unchanged, every CodeDirectory page/resource seal, CMS signer/digest, exact four distribution entitlements, profile/certificate match, both 450-question banks, asset catalogs, privacy manifests and all 15 WAV files per app.
- Both native Watch architectures remain present. The iPhone uses SHA256; Watch signatures retain Xcode's dual SHA1/SHA256 directories. No app binary was injected, removed or substituted.
- Apple processing, approved review, group assignments and live beta states are saved in Artifacts/LocalSigned13RC2/beta-submission.json and beta-availability.json.
- Native symbols remain in the downloaded xcarchive. Apple's build metadata reports includesSymbols=false for this direct upload, unlike build 10; server-side dSYM upload has not been verified. Do not claim full Apple-side symbolication.

## Physical Testing Required

- TestFlight update and launch on the owner's iPhone 16 Pro Max and Watch Ultra 2. Apple availability does not prove installation on either particular device.
- Complete VoiceOver gameplay, next-question focus/speech, real speaker mix with VoiceOver, interruption handling and paired settings delivery.
- Subjective quality and volume of the new loss/victory cues on physical speakers or headphones.
- No formal accessibility conformance or complete physical-device success is inferred from automated tests.

## Release Safeguards

- Owner Testing: 48e2b926-7ee2-4c8a-bed3-8113c9c17209; existing owner tester: 949231b5-e425-42cf-9faa-3b24bbe99371.
- Community Beta: 97d75287-8cd4-44bc-be01-56baeae3401c; enforced public-link limit: 100.
- The previous email-association invitation issue was handled using this existing group's link. Preserve tester identities and memberships; do not substitute another app's tester records.
- The old read-only review monitor targets build 3 and was not changed here. Build 13 is already approved and externally available; no pending review action is required.
- The strict full-cloud gate in beta_metadata.py is unchanged. The separate local route additionally requires native validation, unchanged native content, exact IPA signature/hash checks, matching completed Apple upload and a VALID build before publication.
- Signing/upload secrets remain in the existing protected local directory and encrypted main-only GitHub environment. Never print, commit or move them to another service.
- Use Google Chrome only for any browser authentication. Never use the inaccessible in-app browser. Escape is an NVDA shortcut, not an instruction to stop.

Previous accepted release: 0.1.0 (10), build 3ae613ca-29ef-487a-b4b2-dd62a457a54d, full cloud run 34691414615. Its IPA remains available as a signing-format reference.
