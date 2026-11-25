# 25 November 2026: version 1.0.0 build 52 submitted for public App Store review

Apple confirmed **WAITING_FOR_REVIEW** for Galleonaire 1.0.0 (52) at 2026-11-25T01:05:20Z. The exact version, build and review item were read back from App Store Connect. Automatic release after approval is configured. This is a public App Store submission; no TestFlight group assignment or Beta App Review was requested for this build. Apple approval and public availability are still pending.

The signed iPhone app and embedded Watch app each contain 1,500 questions: the original 1,000 plus 500 additions. This update adds 196 questions (95 intermediate and 101 expert), including 20 at Classic level 15. All additions are shared by Classic and the appropriate exam pools. The 602 intermediate and 630 expert exam questions are a subset of the same 1,500; all twenty papers have pools larger than their paper lengths. New attempts vary selection and order; saved papers remain fixed.

The shared Next Question hint now says “Moves to the next question”. Related wording was corrected for completed-paper Close controls, untimed N.E.W.T. briefings, Classic answer hints and the About screen. Public What's New highlights the larger bank, new O.W.L. and N.E.W.T. modes and clearer Statistics, without presenting the beta-only VoiceOver fix as a public regression. Description, What's New, promotional text and review information were saved and read back. Seven existing App Store screenshots were retained.

Validation passed 98 Python checks, 63 Swift core tests and three focused UI scenarios per platform on Xcode 27.2 (27B52): iPhone 18 Pro Max / iOS 27.2 and Apple Watch Ultra 4 (49mm) / watchOS 27.2. Coverage included Classic entry, O.W.L. answering/navigation/submission/review, N.E.W.T. navigation/save/resume and Statistics with legacy records. The iPhone checks were reused from run 45517229337 after an exact Watch-test-only correction. A stale package-count assertion and a stale Watch Close-label assertion were corrected. The Watch runner did not accept partial scenario reuse, so its three focused scenarios repeated and passed. No full model matrix was repeated. Physical-device VoiceOver speech was unavailable; simulator checks do not establish spoken focus timing.

The archive, signatures, distribution profiles, bundle identifiers, embedded Watch app and exact question-bank contents passed inspection. Upload succeeded at 01:02:29Z, Apple processing completed, and the public review submission succeeded at 01:05:20Z. No further archive or upload is needed for build 52.

- [Successful signed release and upload](https://github.com/sidneytambin-maker/galleonaire-apple/actions/runs/45519137330)
- [Apple public submission and exact status verification](https://github.com/sidneytambin-maker/galleonaire-apple/actions/runs/45522755735)
- Release commit: [be13f7ed3254366fac0693ed1d3f746caacb543c](https://github.com/sidneytambin-maker/galleonaire-apple/commit/be13f7ed3254366fac0693ed1d3f746caacb543c)
- Branch: `codex/public-1500-nov24`, also committed to `main`
- Build UUID: `e87edc32-18bd-44d6-9966-4899e2f13683`
- App Store version UUID: `741d6737-3632-4e6a-9597-611fa6b4b2a4`
- Public review submission UUID: `0674c842-a6dc-4037-adfb-905e377220aa`
- [Exact verification record](Release-52-Verification.json), [editorial/accessibility review](Public-1.0-Editorial-Review.md), and [all twenty paper counts](Exam-Bank-Review.md)

---

# 23 November 2026: build 49 submitted to TestFlight

Galleonaire 0.2.1 (49) has uploaded successfully, finished Apple processing and been submitted to TestFlight. At 2026-11-23T09:24:34Z, Apple reported **IN_BETA_TESTING for Owner Testing** and **WAITING_FOR_BETA_REVIEW for Community Beta**. Both group assignments were read back successfully. External tester availability remains pending Apple's review; the owner's physical TestFlight device listing has not been observed. The current sprint's submission goal is complete. No public App Store release was submitted.

The Apple Developer Program License Agreement issued 29 October 2026 was accepted with the owner's explicit authorization on 23 November 2026 and verified in refreshed account history. The Free Apps Agreement is Active. The previous agreement-related HTTP 403 upload restriction is resolved. Release attempt 3 reported UPLOAD SUCCEEDED with no errors at 09:19:48Z.

The app fixes the changing Skip Question label in both exam types, requests focus on each new question heading and preserves native answer-button actions/roles. Result references open in a detail view and unchanged timer checks avoid unnecessary store updates. Forty sourced questions were added (20 intermediate and 20 expert), screened against the existing bank. All forty also appear in Classic, including eleven at level 15.

The signed iPhone and embedded Watch packages both contain 1,304 unique questions: the original 1,000 plus 304 additions. Of these, 507 intermediate and 529 expert questions are exam-eligible (1,036 in total). All twenty subject/qualification combinations remain supported. Games and papers retain their 15/20/50 question lengths. Existing question objects and saved records are preserved.

Final app verification passed 62 Swift core tests, 95 Python checks and three UI tests per platform on Xcode 27.2 (27B52), iPhone 18 Pro Max / iOS 27.2, and Apple Watch Ultra 4 (49mm) / watchOS 27.2. Build 49 reused the successful native checks from build 48 after an upload-command-only correction supplied the verified Apple app ID. The archive, signatures, distribution profiles, bundle IDs, embedded Watch app and identical reviewed banks passed package inspection. Physical-device VoiceOver speech was unavailable. See the audit for the precise screenshot limitations.

The TestFlight description, testing notes with exact totals, review notes and automatic notifications were saved and read back from Apple. The exact build UUID is `50bac2f3-2a9f-463d-a853-6f8db0624da0`. Beta App Review is WAITING_FOR_REVIEW. The existing Community Beta invitation is https://testflight.apple.com/join/52fmzweP; external access to build 49 depends on Apple approval.

- [Native/product validation](https://github.com/sidneytambin-maker/galleonaire-apple/actions/runs/44969836379)
- [Signed package and successful upload](https://github.com/sidneytambin-maker/galleonaire-apple/actions/runs/44972101334)
- [Successful TestFlight submission and Apple status read-back](https://github.com/sidneytambin-maker/galleonaire-apple/actions/runs/45146058590)
- Release commit: [b4dfec653ed64014ea577361727fd729e64848b2](https://github.com/sidneytambin-maker/galleonaire-apple/commit/b4dfec653ed64014ea577361727fd729e64848b2)
- [Exact verification and release record](Release-49-Verification.json)
- [Accessibility/content audit](VoiceOver-Sprint-Review.md) and [all twenty paper counts](Exam-Bank-Review.md)

No further archive or upload is needed for build 49. App tests were reused without repeating the successful product checks. Apple review timing is outside the project's control; a successful submission is not external tester availability.

---

# Release 42: 7 November 2026

Galleonaire 0.2.0 (42) is APPROVED and IN_BETA_TESTING internally and externally.
The exact valid, unexpired, export-compliant build is assigned to Owner Testing
and Community Beta. Apple reports testing active for both groups.
Apple availability and both group memberships were read back at 2026-11-08T06:43:53.602687+00:00.
Apple beta review is complete. The owner's on-device TestFlight listing has
not been directly observed; server distribution status is not a device check.

Exam Mode provides all ten subjects at O.W.L. and N.E.W.T. level, saved papers,
randomised retakes, neutral answer recording, timed or untimed N.E.W.T. options,
grades and separate answer review. Statistics has been rebuilt around Classic
record, weighted topic performance and separate exam results, with concise accessible
summaries and preserved historical records. The original 1,000 questions are classified
and retained; 264 additions extend the general pool and supply the exam bank.
All twenty papers are supported by 487 intermediate and 509 expert questions.
See [the coverage and editorial review](Exam-Bank-Review.md).

Verification passed 86 Python checks, 61 Swift core tests, 21 iPhone UI tests and
12 Watch UI tests. Representative native checks passed on all 34 supported iPhone
and 13 Watch simulator models using Xcode 27.2, iOS 27.2 and watchOS 27.2. Additional
Duo checks covered outer, inner and partial-fold displays, preserved game/exam state,
results and Statistics at normal and largest accessibility text sizes. Watch AX3
was verified on the 40mm SE 3, including capture comparison with normal text.
Simulator accessibility trees, native audits and screenshots were inspected.
Physical-device VoiceOver speech, audio balance and haptic strength were not tested
because this environment provided no physical devices.

The signed package contains matching reviewed banks in both apps: 1,264 total
questions, of which 996 are exam-eligible. Bundle identifiers and the established
distribution profiles were retained. No public App Store release was submitted.

- Native release commit: [4513a01c1ac88d75b81dbcd14455cf3ab800e1d9](https://github.com/sidneytambin-maker/galleonaire-apple/commit/4513a01c1ac88d75b81dbcd14455cf3ab800e1d9)
- [Signed release workflow](https://github.com/sidneytambin-maker/galleonaire-apple/actions/runs/42338212510)
- [Apple availability workflow](https://github.com/sidneytambin-maker/galleonaire-apple/actions/runs/42338466333)
- Apple build ID: 43411c32-747c-4e42-9a51-6359b01651a6
- [Package, model, bank and Apple read-back evidence](Release-42-Verification.json)
- [Accessibility implementation and verification](Accessibility.md)

---

## Historical build 23 release record: 11 October 2026

Galleonaire 0.1.0 (23) is APPROVED and IN_BETA_TESTING for both Owner Testing and Community Beta. Apple availability, saved testing notes and exact beta-group assignments were verified at 00:06 UTC. No Apple review or account action is pending for this build.

Public invitation: https://testflight.apple.com/join/52fmzweP .

The release adds 250 independently written book questions, giving 1,000 total: 67 at levels 1–10 and 66 at levels 11–15. All previous 750 question objects and migration history remain unchanged. Distinct lifeline effects, green/red answer effects and a million-galleon celebration with a static victory seal are included. Decorative effects respect Reduce Motion and Dim Flashing Lights and do not own input or VoiceOver focus.

All 66 Python checks, 50 native core tests, 16 iPhone UI tests, seven Watch UI tests and embedded archive validation passed. Actual iPhone and Watch simulator screenshots were reviewed, including the victory presentation and accessibility-sized controls. Physical-device VoiceOver speech, haptic strength, audio quality and paired-device settings delivery remain tester checks.

The signed package contains the embedded Watch app and matching reviewed 1,000-question banks in both apps. Distribution profiles were verified and Apple upload succeeded with no errors.

- Native release commit: 1af5fcd2e6dbb8f70ce0f6eed47249044acd0f10
- Release workflow: https://github.com/sidneytambin-maker/galleonaire-apple/actions/runs/38095849903
- Apple availability workflow: https://github.com/sidneytambin-maker/galleonaire-apple/actions/runs/38097135776
- Apple build ID: 96e6cf3a-f05c-4d1c-836f-3e3a1248a6d3
- Question-bank SHA256: fd81be4013831e890eb4800996f3ef2f826f92bcd7401ae66c0fa5883eaed1ff
- Exact package and Apple read-back: Release-23-Verification.json

The workflow's one-time cancellation setting used to replace failed validation attempts has been removed. Subsequent releases remain serialised. Personal contact addresses are absent from the new public metadata; existing contact details remain in App Store Connect. No paid runner or billing changes were made.

---

## Historical build 19 release record

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
