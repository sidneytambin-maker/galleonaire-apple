"""Check the existing Watch smoke flow at Apple's largest watchOS type size."""
import json
import subprocess
import hashlib
from ci import ARTIFACTS, ROOT, ensure_runtime, run, select_xcode

select_xcode()
runtime = ensure_runtime("watchOS")
model = next(d for d in runtime["supportedDeviceTypes"] if d["name"] == "Apple Watch SE 3 (40mm)")
# watchOS simctl reports that its content_size operation is unsupported. Apply
# the standard launch preference in this runner's test harness only. The app
# source stays unchanged; screenshot review must confirm that scaling occurred.
test_path = ROOT / "Apple/WatchUITests/GalleonaireWatchUITests.swift"
original_test = test_path.read_bytes()
test_source = test_path.read_text()
needle = "        app.launch()"
if test_source.count(needle) < 2:
    raise RuntimeError("The existing Watch launch harness changed; inspect it before overriding text size")
test_source = test_source.replace(needle, '        app.launchArguments += ["-UIPreferredContentSizeCategoryName", "UICTContentSizeCategoryAccessibilityXL"]\n' + needle)
test_path.write_text(test_source)
run("generate-project", ["xcodegen", "generate", "--spec", "Apple/project.yml", "--project", "Apple"])
base = ["xcodebuild", "-project", "Apple/Galleonaire.xcodeproj", "-scheme", "GalleonaireWatch",
        "CODE_SIGNING_ALLOWED=NO", "-derivedDataPath", str(ROOT / ".watch-large-text-build"),
        "-parallel-testing-enabled", "NO"]
run("watch-large-text-build", base + ["-destination", "generic/platform=watchOS Simulator", "build-for-testing"])
device = subprocess.check_output(["xcrun", "simctl", "create", "Galleonaire Watch AX3", model["identifier"], runtime["identifier"]], text=True).strip()
result = ARTIFACTS / "watch-large-text.xcresult"
try:
    subprocess.run(["xcrun", "simctl", "boot", device], check=True, timeout=60)
    subprocess.run(["xcrun", "simctl", "bootstatus", device, "-b"], check=True, timeout=300)
    run("watch-large-text-smoke", base + ["-destination", "id=" + device,
        "-resultBundlePath", str(result),
        "-only-testing:GalleonaireWatchUITests/GalleonaireWatchUITests/testSupportedModelClassicExamAndStatisticsSmoke",
        "test-without-building"])
    summary = json.loads(subprocess.check_output(["xcrun", "xcresulttool", "get", "test-results", "summary", "--path", str(result)]))
    if summary.get("totalTestCount") != 1 or summary.get("passedTests") != 1:
        raise RuntimeError("The Watch AX3 smoke test did not execute and pass exactly once")
    report = {"passed": True, "model": model["name"], "runtime": runtime["version"],
              "runtimeBuild": runtime["buildversion"], "requestedAppleTextSize": "AX3",
              "overrideRoute": "UI test launch preference", "fontScalingRequiresCaptureReview": True,
              "originalTestSHA256": hashlib.sha256(original_test).hexdigest(),
              "physicalVoiceOverTested": False,
              "checks": ["Classic entry", "saved exam through result", "single close control", "legacy accuracy summary"]}
    (ARTIFACTS / "watch-large-text-verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2), flush=True)
finally:
    test_path.write_bytes(original_test)
    if result.exists():
        run("watch-large-text-attachments", ["xcrun", "xcresulttool", "export", "attachments", "--path", str(result),
                                             "--output-path", str(ARTIFACTS / "watch-large-text-attachments")])
    for action in ["shutdown", "delete"]:
        try: subprocess.run(["xcrun", "simctl", action, device], capture_output=True, timeout=30)
        except subprocess.TimeoutExpired: print("Simulator cleanup timed out: " + action, flush=True)
