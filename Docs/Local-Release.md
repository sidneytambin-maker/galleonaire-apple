# Verified Local Release of Build 13

The cloud Mac completed all native tests and an unsigned Release archive in run 34723039177. GitHub refused to start the separate signing job because of an account billing/spending restriction. This document records the free local signing/upload path actually used, not a claim that the failed cloud workflow succeeded.

## Gates

1. Require the exact main-branch TestFlight workflow and successful validation job, with 38 Swift, 13 iPhone and six Watch tests passed and no skips.
2. Require the tested source revision to remain an ancestor of HEAD, with no changes to native code, reviewed question content or native test runner.
3. Start from the downloaded xcarchive, preserving all native architectures, code/data sections, resources and Watch placement. Change only both distribution build numbers to 13.
4. Retrieve the existing active Galleonaire App Store profiles directly from Apple. Match team, app identifiers, distribution certificate, expiration and beta/debug entitlements. Never use a profile from another app.
5. Sign Watch first, then its containing iPhone app, using rcodesign 0.29.0 with direct per-app entitlements and shallow signing. Native platform targeting selects compatible code digests. No remote signing service is used.
6. Verify native sections, resource seals, CodeDirectory pages and special slots, full CMS signatures against the exact distribution certificate, four required entitlements and both packaged question banks. These checks do not impersonate macOS codesign trust evaluation.
7. Submit to Apple's buildUploads API. Check exact app/version/build, restrict upload destinations and redirects, and verify every received part's entity tag against the local bytes. Keep the IPA's SHA256 in the local receipt.
8. Require Apple upload COMPLETE, a matching build relationship, processing VALID, no expiry and confirmed export compliance before assigning tester groups or submitting beta review.
9. Read back metadata, exact group membership, approved review, automatic notification and actual IN_BETA_TESTING states. Never call a merely uploaded or submitted build live.

## Tools and Dependencies

- Scripts/local_sign.py prepares and signs a fresh output directory.
- Scripts/inspect_local_ipa.py and macho_seals.py independently verify the produced package.
- Scripts/direct_upload.py uploads/resumes the identical package and reads Apple processing.
- Scripts/local_beta.py publishes only after all local and Apple gates pass, using the existing metadata/review helpers. Their strict cloud gate remains unchanged.
- Python cryptography is needed only for actual signing/Apple authentication. All 57 local regression tests also pass with third-party site packages disabled.
- rcodesign 0.29.0 was downloaded from its official GitHub release; its archive checksum was checked against the publisher's SHA256 file. Its license remains with the local downloaded tool. No tool binary or private signing material is committed.
- The existing encrypted P12/password and App Store Connect key are read from their protected directory. Temporary entitlement files are removed after signing. Logs never contain passwords or signed upload URLs.

## Failure Record

- The first optional sourceFileChecksums request was rejected. Apple's reservation supplied no whole-file checksum. The corrected commit omits that optional attribute, matching the API schema and upstream uploader, while independently verifying the received parts and local SHA256.
- zsign SHA256-only output passed local content/CMS checks but Apple rejected the Watch signature with 90035. Dual-hash zsign output was then rejected with 90034. Those rejected artifacts are not distribution candidates.
- Comparing the accepted Xcode build 10 revealed platform-specific digest and entitlement differences. The final rcodesign package uses the same four required application entitlements and platform-derived digests. The exact internal cause of each earlier Apple rejection is not claimed beyond Apple's returned error codes.
- Scoped entitlement paths in the first Windows rcodesign attempt did not reach the executables. Local verification caught this before upload. Signing each bundle directly fixed the issue without moving Watch or altering native code.
- Final output Artifacts/LocalSigned13RC2/Galleonaire.ipa passed local inspection and Apple processing. Apple approved build 13 and made it available to both existing tester groups.
- Failed artifacts remain distinct for diagnostics. Do not install or upload LocalSigned13, LocalSigned13Dual, LocalSigned13RC or the incomplete LocalRelease13 directory.

## Evidence and Limits

Accepted IPA SHA256: ee5c205f9728d35b3fb345fafe239ac846991b7e7fbbc01840437ec5a229a22b.

Native evidence: Artifacts/Run34723039177/galleonaire-release-tests-13. Final signing/upload/availability receipts: Artifacts/LocalSigned13RC2.

Apple reports includesSymbols=false for this direct upload. The native xcarchive and dSYMs are retained locally; a successful Apple-side symbol upload has not been demonstrated. Physical installation, actual VoiceOver speech/focus and hardware audio remain user-device tests.

## References

- [Apple build uploads API](https://developer.apple.com/documentation/appstoreconnectapi/build-uploads)
- [Apple API OpenAPI specification](https://developer.apple.com/sample-code/app-store-connect/app-store-connect-openapi-specification.zip)
- [Apple's API upload workflow presentation](https://developer.apple.com/videos/play/wwdc2025/324/)
- [Upstream upload commit implementation](https://github.com/rudrankriyam/App-Store-Connect-CLI/blob/main/internal/cli/shared/build_uploads.go)
- [Upstream optional-checksum selection](https://github.com/rudrankriyam/App-Store-Connect-CLI/blob/main/internal/cli/builds/builds_commands.go)
- [Apple Codesign documentation](https://gregoryszorc.com/docs/apple-codesign/stable/apple_codesign.html)
- [Official rcodesign 0.29.0 release](https://github.com/indygreg/apple-platform-rs/releases/tag/apple-codesign%2F0.29.0)
