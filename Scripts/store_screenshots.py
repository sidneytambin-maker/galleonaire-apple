"""Capture the unchanged released game through existing native UI tests."""
import argparse
import subprocess
from ci import ROOT, ARTIFACTS, select_xcode, run, simulator

parser = argparse.ArgumentParser()
parser.add_argument("--device", choices=["phone", "ipad", "watch"], required=True)
args = parser.parse_args()
select_xcode()
run("generate-project", ["xcodegen", "generate", "--spec", "Apple/project.yml", "--project", "Apple"])
watch = args.device == "watch"
device = simulator("watchOS" if watch else "iOS", "Apple Watch" if watch else "iPad Pro (13-inch" if args.device == "ipad" else "iPhone")
subprocess.run(["xcrun", "simctl", "boot", device], capture_output=True)
run("boot", ["xcrun", "simctl", "bootstatus", device, "-b"])
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
