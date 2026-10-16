"""Capture the unchanged released game through existing native UI tests."""
import argparse
import json
import re
import subprocess
from ci import ROOT, ARTIFACTS, select_xcode, run, simulator

parser = argparse.ArgumentParser()
parser.add_argument("--device", choices=["phone", "ipad", "watch"], required=True)
args = parser.parse_args()
select_xcode()
run("generate-project", ["xcodegen", "generate", "--spec", "Apple/project.yml", "--project", "Apple"])
watch = args.device == "watch"
if args.device == "ipad":
    inventory = json.loads(subprocess.check_output(["xcrun", "simctl", "list", "--json"]))
    types = [item for item in inventory["devicetypes"] if "iPad Pro" in item["name"] and ("13-inch" in item["name"] or "12.9-inch" in item["name"])]
    runtimes = [item for item in inventory["runtimes"] if item.get("isAvailable") and "iOS" in item["name"]]
    if not types or not runtimes:
        raise RuntimeError("A large iPad device type and iOS runtime are required")
    device_type = sorted(types, key=lambda item: ("13-inch" in item["name"], item["name"]))[-1]
    runtime = max(runtimes, key=lambda item: tuple(map(int, re.findall(r"\d+", item["version"]))))
    device = subprocess.check_output(["xcrun", "simctl", "create", "Galleonaire Store iPad", device_type["identifier"], runtime["identifier"]], text=True).strip()
    print("Created " + device_type["name"] + " on " + runtime["name"], flush=True)
else:
    device = simulator("watchOS" if watch else "iOS", "Apple Watch" if watch else "iPhone")
subprocess.run(["xcrun", "simctl", "boot", device], capture_output=True)
run("boot", ["xcrun", "simctl", "bootstatus", device, "-b"])
if not watch:
    subprocess.run(["xcrun", "simctl", "status_bar", device, "override", "--time", "9:41", "--batteryState", "charged", "--batteryLevel", "100"], check=True)
scheme = "GalleonaireWatch" if watch else "Galleonaire"
suite = "GalleonaireWatchUITests/GalleonaireWatchUITests" if watch else "GalleonaireUITests/GalleonaireUITests"
tests = ["testIndependentWatchGameAdvancesCorrectAnswersImmediately", "testWatchTabsSwapQuestionAndSettingsPreserveGame", "testWatchMillionPrizeAndReturnToMenu"] if watch else ["testCorrectAnswerAdvancesImmediatelyWithSeparateVoiceOverFeedback", "testFiftyFiftyRemovesButtonsAndAudienceVotesAreInsideRemainingAnswers", "testMillionGalleonsHasCelebrationAndReturnsToMenu"]
if args.device == "phone":
    tests += ["testFourBottomTabsAndSingleFirstGameHeading", "testStatisticsUpdateAndPersistWithoutDecorativeChartElements", "testHomeAccessibilityAudit"]
result = ARTIFACTS / "Store.xcresult"
command = ["xcodebuild", "-project", "Apple/Galleonaire.xcodeproj", "CODE_SIGNING_ALLOWED=NO", "-scheme", scheme, "-destination", "id=" + device, "-parallel-testing-enabled", "NO", "-resultBundlePath", str(result), "test"]
command += ["-only-testing:" + suite + "/" + name for name in tests]
try:
    run("store-screenshots", command)
finally:
    if result.exists():
        run("export-screenshots", ["xcrun", "xcresulttool", "export", "attachments", "--path", str(result), "--output-path", str(ARTIFACTS / "screenshots")])
        run("test-summary", ["xcrun", "xcresulttool", "get", "test-results", "summary", "--path", str(result)])
