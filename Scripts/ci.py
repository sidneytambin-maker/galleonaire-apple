"""Build and test real Apple targets, preserving logs and simulator evidence."""
import argparse
import json
import plistlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "Artifacts"


def run(name, command, cwd=ROOT):
    print(f"Starting {name}", flush=True)
    ARTIFACTS.mkdir(exist_ok=True)
    with (ARTIFACTS / f"{name}.log").open("w", encoding="utf-8") as log:
        process = subprocess.Popen(command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            print(line, end="", flush=True)
            log.write(line)
        code = process.wait()
    if code: raise SystemExit(f"{name} failed with exit code {code}")


def simulator(platform, name):
    result = json.loads(subprocess.check_output(["xcrun", "simctl", "list", "devices", "available", "--json"]))
    candidates = [(runtime, d) for runtime, devices in result["devices"].items() if platform in runtime for d in devices if name in d["name"]]
    if not candidates: raise SystemExit(f"No {platform} {name} simulator is installed")
    runtime, device = sorted(candidates, key=lambda x: (x[0], x[1]["name"]), reverse=True)[0]
    print(f"Testing {device['name']} on {runtime}", flush=True)
    return device["udid"]


def verify_archive(path):
    phone = path / "Products/Applications/Galleonaire.app"
    watch = phone / "Watch/GalleonaireWatch.app"
    assert phone.is_dir() and watch.is_dir(), "Watch must be embedded in the iPhone app's Watch directory"
    info = plistlib.loads((phone / "Info.plist").read_bytes())
    watch_info = plistlib.loads((watch / "Info.plist").read_bytes())
    assert info["CFBundleIdentifier"] == "com.inclusophy.galleonaire"
    assert watch_info["CFBundleIdentifier"] == "com.inclusophy.galleonaire.watchkitapp"
    assert watch_info["WKCompanionAppBundleIdentifier"] == info["CFBundleIdentifier"]
    assert watch_info["WKApplication"] is True
    assert info["CFBundleVersion"] == watch_info["CFBundleVersion"]
    assert info["CFBundleShortVersionString"] == watch_info["CFBundleShortVersionString"]
    for app in [phone, watch]:
        assert (app / "Assets.car").exists(), "Missing compiled icons"
        assert (app / "magical-library.wav").exists(), "Missing background music"
        assert any(app.rglob("questions.json")), "Missing question resource bundle"
        assert (app / "PrivacyInfo.xcprivacy").exists(), "Missing privacy manifest"
    (ARTIFACTS / "archive-verification.json").write_text(json.dumps({"phoneBundle": info["CFBundleIdentifier"], "watchBundle": watch_info["CFBundleIdentifier"], "version": info["CFBundleShortVersionString"], "build": info["CFBundleVersion"], "watchEmbedded": True, "signed": False}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=["all", "unit", "phone", "watch", "archive"], default="all")
    args = parser.parse_args()
    run("xcode-version", ["xcodebuild", "-version"])
    if args.stage in ["all", "unit"]: run("core-tests", ["swift", "test", "--package-path", "Apple"])
    if args.stage == "unit": raise SystemExit(0)
    run("generate-project", ["xcodegen", "generate", "--spec", "Apple/project.yml", "--project", "Apple"])
    base = ["xcodebuild", "-project", "Apple/Galleonaire.xcodeproj", "CODE_SIGNING_ALLOWED=NO"]
    if args.stage in ["all", "phone"]:
        run("iphone-ui-tests", base + ["-scheme", "Galleonaire", "-destination", "id=" + simulator("iOS", "iPhone"), "-parallel-testing-enabled", "NO", "-resultBundlePath", str(ARTIFACTS / "iPhone.xcresult"), "test"])
    if args.stage in ["all", "watch"]:
        run("watch-ui-tests", base + ["-scheme", "GalleonaireWatch", "-destination", "id=" + simulator("watchOS", "Apple Watch"), "-parallel-testing-enabled", "NO", "-resultBundlePath", str(ARTIFACTS / "Watch.xcresult"), "test"])
    if args.stage in ["all", "archive"]:
        path = ARTIFACTS / "Galleonaire.xcarchive"
        run("release-archive", base + ["-scheme", "Galleonaire", "-configuration", "Release", "-destination", "generic/platform=iOS", "-archivePath", str(path), "archive"])
        verify_archive(path)
