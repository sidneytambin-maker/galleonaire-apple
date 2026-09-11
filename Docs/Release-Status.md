# Galleonaire Release Status

Last verified: 11 September 2026.

## Current Release

- Personal project name: Galleonaire. No company branding. Court Story and the original handheld reference were not modified.
- Version 0.1.0 (3) was uploaded to Apple and processed successfully.
- App Store Connect app: 6811170867, bundle com.sidneytambin.galleonaire.
- Apple build: 1dfb0435-ed37-4782-9680-d0ec130b7ff1, processingState VALID, expired false, usesNonExemptEncryption false.
- TestFlight internalBuildState: IN_BETA_TESTING.
- Owner Testing has the exact build and Sidney Tambin as its internal tester. Chrome independently shows Invited. Invitation acceptance and installation are not yet verified.
- Community Beta has the exact build. External Beta App Review was submitted and read back as WAITING_FOR_REVIEW. Chrome independently shows Waiting for Review.
- Automatic tester notification is enabled and verified. No public App Store release was submitted.
- No external public link has been enabled or delivered. External testing must not be described as live before Apple approves it.

## Build and Test Evidence

- Private repository: sidneytambin-maker/galleonaire-apple, main branch.
- Successful full TestFlight Release run: 34644073674, source revision 0a65f1a, upload=true.
- All 25 shared Swift tests, seven iPhone UI tests, two Watch UI tests and 31 Python regression tests passed.
- Release archive, distribution signing, strict signature validation, IPA inspection and actual Apple upload passed.
- Downloaded IPA: Artifacts/Run-34644073674/galleonaire-testflight-package-3/TestFlight/Galleonaire.ipa.
- IPA SHA256: e1f0828cdf96725fed2c82d8b218f7663dd9f42ad9e86a8bc5b4da1669979290.
- signed-package-verification.json records uploaded=true, watchEmbedded=true and distributionProfilesVerified=true.
- Independent local IPA inspection confirms both apps are named Galleonaire, both have version 0.1.0/build 3, and the Watch companion points to com.sidneytambin.galleonaire.
- Apple Build Metadata shows Binary State Validated, Device Family iPhone, iPad, Apple Watch, and both signed executable entitlements, including Galleonaire.app/Watch/GalleonaireWatch.app/GalleonaireWatch.
- Minimum versions: iOS 17 and watchOS 10.
- Native evidence: Artifacts/Run-34644073674/galleonaire-release-tests-3, including xcresults, summaries, screenshots and accessibility trees.
- Current largest-text iPhone and Watch gameplay screenshots were inspected. Answer-letter and answer-text columns remain separate; long text scrolls without overlapping.
- Simulator coverage uses iPhone 17 Pro Max and Apple Watch Ultra 3, not Sidney's physical iPhone 16 Pro Max and Apple Watch Ultra 2.

## Implemented and Verified in Code or Simulator

- Shared game rules, original 300-question migration, progression, all three lifelines, winning/losing/walking away, persistence and independent device games.
- Native accessible answer states, custom actions, focus management, dialogs, Settings, volume controls and game restoration.
- Original icon, background music and eleven distinct event sounds, with retained provenance and actual-media regression tests.
- Persistent audio/haptic preferences and conflict-resolving settings synchronization logic.
- Largest accessibility text layout, home accessibility audit, Settings/cancellation/resume, answer/result flows, Watch scrolling and Free Pass.
- Full native validation gates release. Cloud signing uses an ephemeral keychain and cleans up installed profiles and signing material.

## Physical Testing Still Required

- Actual TestFlight installation and launch on Sidney's iPhone and Watch.
- Complete VoiceOver gameplay and real focus/rotor behaviour on both physical devices.
- Audio intelligibility while VoiceOver speaks, hardware haptics, interruption/resume and actual paired-device settings delivery.
- No formal accessibility conformance or complete physical-device success is claimed from automated tests alone.

## Apple Review Follow-Up

- Internal group: 48e2b926-7ee2-4c8a-bed3-8113c9c17209.
- Internal beta tester: 949231b5-e425-42cf-9faa-3b24bbe99371. Do not substitute the separate external tester record from another app.
- External group: 97d75287-8cd4-44bc-be01-56baeae3401c.
- Desired external public-link limit: 100 testers, as recorded in TestFlight-Metadata.json. Deliver the link to Sidney only, not publicly elsewhere.
- Heartbeat automation galleonaire-review-status checks review status hourly. It is explicitly read-only and reports meaningful changes only.
- A proposed background automation that would also change tester access was rejected by safety review. It was not created. The read-only alternative does not enable a public link or change distribution.
- Once approved, verify the exact build, review state and external availability before enabling the public link. Verify the saved tester limit and working URL before reporting external testing live. Do not cancel or blindly resubmit pending/rejected review.
- Scripts/beta_metadata.py and Scripts/beta_release.py have now succeeded against the live Galleonaire app. Both groups and testing notes were saved and independently read back; review submission was confirmed by API and Chrome.
- Existing signing/upload secrets remain encrypted in the main-only testflight environment. Do not expose or relocate credentials. Reuse the existing App Store Connect key in the protected local testflight-distribution-private directory through Scripts/apple_accounts.py; never print its contents.

Use Google Chrome only for browser interaction or authentication. Never reopen the inaccessible in-app browser. Escape is an NVDA shortcut, not a user request to stop development. The user has repeatedly authorised this project's development and TestFlight publication; do not invent another general permission requirement.

Apple references:
- https://developer.apple.com/help/app-store-connect/test-a-beta-version/add-internal-testers
- https://developer.apple.com/help/app-store-connect/test-a-beta-version/invite-external-testers
- https://developer.apple.com/documentation/appstoreconnectapi/build-beta-details
