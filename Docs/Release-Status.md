# Galleonaire Release Status

Last verified: 12 September 2026, 11:52 UTC.

## Current Release

- Personal project name: Galleonaire. No company branding. Court Story and the original handheld reference were not modified.
- Version 0.1.0 (10) was uploaded to Apple and processed successfully.
- App Store Connect app: 6811170867, bundle com.sidneytambin.galleonaire.
- Apple build: 3ae613ca-29ef-487a-b4b2-dd62a457a54d, processingState VALID, expired false, usesNonExemptEncryption false.
- TestFlight internalBuildState: IN_BETA_TESTING.
- Owner Testing and Community Beta both contain the exact build 10. Existing tester identities and memberships were preserved.
- Community Beta has the exact build. Apple Beta App Review is APPROVED and the external build state is IN_BETA_TESTING, independently read back from the API on 12 September.
- Automatic tester notification is enabled and verified. No public App Store release was submitted.
- The existing Community Beta public invitation link remains enabled with its enforced limit of 100 testers, independently read back from Apple. No new audience, public link or invitation was created for this update.

## Invitation Recovery, 12 September

- Sidney reported an Apple Account/email-association error from the previous invitation and requested a working download route.
- The internal tester email matches the verified owner email. The API does not expose the device's current Apple Account association, so the exact cause of that mismatch is not claimed as proven.
- Preserved the existing internal tester record and memberships. No Apple Account settings or Court Story access were changed.
- Enabled the already approved external group's public joining link, with the saved 100-tester limit, to provide an alternative that does not reuse the old email-bound invitation.
- Verified the exact app, approved build, external group assignment, saved limit, active link and working Apple join page. The link itself is not copied into source control; retrieve it from this group's App Store Connect record when needed.
- Sent "Your new Galleonaire TestFlight download link" to the verified owner email. Delivery was confirmed by the returned SENT and INBOX labels. This was a download-link email, not a claim that Apple reissued an internal invitation.
- Installation and launch using the new link on the user's particular iPhone and Watch still require device confirmation. No new binary or rebuild was required for this access correction.

## Build and Test Evidence

- Private repository: sidneytambin-maker/galleonaire-apple, main branch.
- Successful full TestFlight Release run: 34691414615, source revision 8296c95, upload=true.
- All 82 tests passed: 34 shared Swift tests, 11 iPhone UI tests, four Watch UI tests and 33 Python regression tests. No tests were skipped to release.
- Release archive, distribution signing, strict signature validation, IPA inspection and actual Apple upload passed.
- Downloaded IPA: Artifacts/Run34691414615/package/TestFlight/Galleonaire.ipa.
- IPA SHA256: f8574be6c68106bf1d1194c53bf0508f5070b4cfb6631588136c65ea5396c03e.
- signed-package-verification.json records uploaded=true, watchEmbedded=true and distributionProfilesVerified=true.
- Independent local IPA inspection confirms both apps are named Galleonaire, both have version 0.1.0/build 10, and the Watch companion points to com.sidneytambin.galleonaire. ZIP integrity, both compiled asset catalogs, privacy manifests, signatures and all 15 WAV resources per app were checked.
- The actual Watch app is embedded at Payload/Galleonaire.app/Watch/GalleonaireWatch.app. Strict code-signature and App Store distribution profile validation passed on the cloud Mac before upload.
- Minimum versions: iOS 17 and watchOS 10.
- Native evidence: Artifacts/Run34691414615, including xcresults, summaries, screenshots and accessibility trees. The final volume screenshot shows both sliders at 100%; the test also verified exact zero, intermediate changes in both directions and persistence after relaunch.
- Current largest-text iPhone and Watch gameplay screenshots were inspected. Answer-letter and answer-text columns remain separate; long text scrolls without overlapping.
- Simulator coverage uses iPhone 17 Pro Max and Apple Watch Ultra 3, not Sidney's physical iPhone 16 Pro Max and Apple Watch Ultra 2.

## Implemented and Verified in Code or Simulator

- Shared game rules, original 300-question migration, progression, all three lifelines, winning/losing/walking away and independent device games.
- Three bottom tabs: Game, How to play, Settings. One combined first heading names Galleonaire. Original emerald/gold artwork, compact default typography and prize-progress visuals preserve native text scaling and VoiceOver semantics.
- Answer activation immediately scores, without selection/locking/confirmation. A combined top result contains outcome, correct answer and explanation, followed by Next Question. Focus is requested on that result and then the next question.
- Main Menu and Play Again after terminal results. Every fresh process launch discards the game, including old-version saves, while preserving highest prize, question history and settings. Switching tabs or briefly backgrounding a still-running process keeps the current game.
- Fifty-Fifty removes wrong answer buttons, audience votes appear inside each surviving answer, and Swap Question replaces the old Free Pass label while retaining the compatible saved identifier.
- Full 0-100% music/effects gain without VoiceOver ceilings. Nine independent sound preview buttons, contrasting correct/incorrect sounds, synthesized audience applause and distinct Fifty-Fifty/Swap Question cues. Original assets and provenance are retained; 15 WAV files are packaged per app, including legacy unused cues.
- Persistent audio/haptic preferences and conflict-resolving settings synchronization logic.
- Largest accessibility text layout, home accessibility audit, Settings/cancellation, cold-launch reset, answer/result flows and Watch scrolling all have native test coverage.
- Full native validation gates release. Cloud signing uses an ephemeral keychain and cleans up installed profiles and signing material.

## Physical Testing Still Required

- Actual TestFlight update to build 10 and launch on Sidney's iPhone and Watch. Apple confirms availability, not physical installation of this new build.
- Complete VoiceOver gameplay and real focus/rotor behaviour on both physical devices.
- Audio intelligibility while VoiceOver speaks, hardware haptics, interruption/resume and actual paired-device settings delivery.
- No formal accessibility conformance or complete physical-device success is claimed from automated tests alone.

## Apple Review Follow-Up

- Internal group: 48e2b926-7ee2-4c8a-bed3-8113c9c17209.
- Internal beta tester: 949231b5-e425-42cf-9faa-3b24bbe99371. Do not substitute the separate external tester record from another app.
- External group: 97d75287-8cd4-44bc-be01-56baeae3401c.
- Verified enforced external public-link limit: 100 testers, as recorded in TestFlight-Metadata.json. The link was delivered to Sidney only; Sidney can share it with chosen testers.
- The existing read-only hourly galleonaire-review-status monitor was configured for build 3 and was not changed by this update. Build 10 is already APPROVED and IN_BETA_TESTING externally; no pending review or future distribution action is required for this release.
- A proposed background automation that would also change tester access was rejected by safety review. It was not created. The read-only alternative does not enable a public link or change distribution.
- The public link was enabled during Sidney's active invitation-recovery request, not by the read-only heartbeat. Future access changes must still verify the exact build, approval, saved tester limit and working URL. Do not cancel or blindly resubmit review.
- Scripts/beta_metadata.py and Scripts/beta_release.py succeeded for build 10 against the live Galleonaire app. Updated description, review notes, both groups and testing notes were saved and independently read back; APPROVED review and both IN_BETA_TESTING states were confirmed by API.
- Existing signing/upload secrets remain encrypted in the main-only testflight environment. Do not expose or relocate credentials. Reuse the existing App Store Connect key in the protected local testflight-distribution-private directory through Scripts/apple_accounts.py; never print its contents.

Use Google Chrome only for browser interaction or authentication. Never reopen the inaccessible in-app browser. Escape is an NVDA shortcut, not a user request to stop development. The user has repeatedly authorised this project's development and TestFlight publication; do not invent another general permission requirement.

Apple references:
- https://developer.apple.com/help/app-store-connect/test-a-beta-version/add-internal-testers
- https://developer.apple.com/help/app-store-connect/test-a-beta-version/invite-external-testers
- https://developer.apple.com/documentation/appstoreconnectapi/build-beta-details
