"""Check the existing Watch smoke flow at Apple's largest watchOS type size."""
import json
import subprocess
from ci import ARTIFACTS, ROOT, ensure_runtime, run, select_xcode

select_xcode()
runtime = ensure_runtime("watchOS")
model = next(d for d in runtime["supportedDeviceTypes"] if d["name"] == "Apple Watch SE 3 (40mm)")
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
    # Apple's watchOS typography table ends at AX3 (Accessibility Extra Large).
    size = "accessibility-extra-large"
    subprocess.run(["xcrun", "simctl", "ui", device, "content_size", size], check=True, timeout=30)
    actual = subprocess.check_output(["xcrun", "simctl", "ui", device, "content_size"], text=True, timeout=30).strip()
    if actual != size:
        raise RuntimeError("The Watch simulator did not retain the requested AX3 text size: " + actual)
    run("watch-large-text-smoke", base + ["-destination", "id=" + device,
        "-resultBundlePath", str(result),
        "-only-testing:GalleonaireWatchUITests/GalleonaireWatchUITests/testSupportedModelClassicExamAndStatisticsSmoke",
        "test-without-building"])
    summary = json.loads(subprocess.check_output(["xcrun", "xcresulttool", "get", "test-results", "summary", "--path", str(result)]))
    if summary.get("totalTestCount") != 1 or summary.get("passedTests") != 1:
        raise RuntimeError("The Watch AX3 smoke test did not execute and pass exactly once")
    report = {"passed": True, "model": model["name"], "runtime": runtime["version"],
              "runtimeBuild": runtime["buildversion"], "contentSize": actual, "appleTextSize": "AX3",
              "physicalVoiceOverTested": False,
              "checks": ["Classic entry", "saved exam through result", "single close control", "legacy accuracy summary"]}
    (ARTIFACTS / "watch-large-text-verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2), flush=True)
finally:
    if result.exists():
        run("watch-large-text-attachments", ["xcrun", "xcresulttool", "export", "attachments", "--path", str(result),
                                             "--output-path", str(ARTIFACTS / "watch-large-text-attachments")])
    for action in ["shutdown", "delete"]:
        try: subprocess.run(["xcrun", "simctl", action, device], capture_output=True, timeout=30)
        except subprocess.TimeoutExpired: print("Simulator cleanup timed out: " + action, flush=True)
