# Current release: 24 September 2026

Galleonaire 0.1.0 (19) is APPROVED and IN_BETA_TESTING for both Owner Testing and Community Beta. Apple processing is VALID, the build is unexpired, and export compliance is confirmed. Independently verified at 21:30 UTC (22:30 UK time). Automatic tester notifications are enabled. The saved tester notes and both group assignments were read back successfully. No Apple review or account action is pending.

Native commit: 60851afad12bad00f0d6ad8c560c67e57f8bac34. Free standard public Mac workflow: https://github.com/sidneytambin-maker/galleonaire-apple/actions/runs/36058891945 . All 62 local checks, 50 native core tests, 16 iPhone tests, seven Watch tests and archive validation passed. Actual simulator screenshots were reviewed, including default and accessibility-sized text. Physical VoiceOver speech, audio quality, haptic strength and paired-device settings delivery remain real-device checks, clearly requested in tester notes.

The signed package embeds the Watch app and the same reviewed 750-question bank in each app. Signing verification and upload succeeded with no errors. Original media, revised questions/difficulty, history migration, statistics, prize ladder, lifeline visuals and stronger loss haptics are included. Audio mixing is unchanged. Normal text is the default; semantic fonts follow the user's system settings.

Apple reports 41 community testers plus one owner, all app-level INSTALLED. New build 19 currently reports 0 installs, 0 sessions, 0 crashes and 0 feedback, with inviteCount 42. Build 16 reports 30 installs and 35 sessions; build 13 reports 34 installs and 96 sessions; build 10 reports 2 installs and 5 sessions; build 3 reports 2 installs and 8 sessions. All report zero crashes and feedback. Per-build installs are not unique-person totals. No separate download figure is inferred.

Screenshot feedback: 0. Crash feedback: 0. No submitted feedback awaits action. For 25 August–24 September, Apple reports 42 public-link views, 39 acceptances, 0 did-not-accept and 0 criteria failures; do not infer additional outcomes from the differing totals. The public invitation remains enabled with its optional group cap disabled: https://testflight.apple.com/join/52fmzweP . Apple's platform maximum still applies.

Apple build ID: b7332f08-56d0-4ef2-8b37-cefe90871e51.
IPA SHA256: b0fe8b2c00a9f79924829eac661abd3f1014a1cff06329f477c1bdc59c0e6313.
Evidence: Artifacts/Release19Unit, Release19Phone, Release19Watch, Release19Archive and Release19Package. Source history and public test/package logs passed redacted secret scans; private account/contact records remain outside the repository. No paid usage or billing changes were enabled.

---

## Historical build 16 release record

# Current release: 23 September 2026

Galleonaire 0.1.0 (16) is APPROVED and IN_BETA_TESTING internally and externally.
Apple processing is VALID. Both Owner Testing and Community Beta contain this exact
build; automatic notification is enabled. Revised tester notes thank the community,
explain the game and test steps, and clearly explain independent music/effects
switches, 0–100% volume controls, complete muting, sound previews and haptics.

Live build ID: 1afe6d49-9dc6-4199-a71b-5eefd7a295a0.
Successful full release run: 35890216744, attempt 2, source f6d5afc.
58 Python, 42 Swift, 13 iPhone UI and 6 Watch UI tests passed, with no native skips.
Both native apps contain the identical 600-question reviewed bank. Simulator
screenshots were inspected; physical VoiceOver speech and hardware audio still need
beta testing. Upload and Apple processing completed with no errors.

Shipped: separate VoiceOver feedback/question elements and revised focus; 150 added
questions (600 total, 40 per level); 263 existing contextual clarifications; persistent
shuffling without consecutive correct-position repeats; original enchanted-library
artwork and accessible green/red edge pulses. See Question-Review-600.md and Accessibility.md.

The repository is PUBLIC with explicit user authorisation. Free standard Mac runners
completed the release. No paid usage was enabled. The earlier billing blocker is
resolved by this authorised public-build route. The initial long attempt was cancelled;
independent Swift, archive and iPhone checks passed, and the subsequent full run passed.

Verified 17:55 UTC: 34 enrolled testers (1 Owner Testing, 33 Community Beta), all app-level
INSTALLED; screenshot feedback 0 and crash feedback 0. Build 16 usage is 0 installs,
0 sessions, 0 crashes and 0 feedback at that check. These are distinct from enrollment.
No Apple review or account action is pending for this release.

IPA SHA256: f1c2e86a262a3969b76b2be9a27ab94ec7f4b411126b12f8d1727abef147ed3e.
Evidence: Artifacts/Release16Validation and Artifacts/Release16Package.

---

## Historical build 13 release record

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

Open-access update, 23 September 2026: at the user's request, Community Beta's
optional 100-person limit is now disabled and recruitment criteria are absent.
The existing public link is unchanged. Code-free joining instructions were saved
to the public beta description and independently read back. See TestFlight-Access.md.
