"""Build and test real Apple targets, preserving logs and simulator evidence."""
import argparse
import json
import plistlib
import subprocess
import re
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "Artifacts"


def select_xcode():
    candidates = []
    for app in Path("/Applications").glob("Xcode*.app"):
        if "beta" in app.name.lower(): continue
        info = app / "Contents/Info.plist"
        if not info.exists(): continue
        version = plistlib.loads(info.read_bytes()).get("CFBundleShortVersionString", "0")
        numbers = tuple(map(int, re.findall(r"\d+", version)))
        if numbers and numbers[0] >= 26: candidates.append((numbers, app))
    if not candidates: raise RuntimeError("Apple uploads require a stable Xcode 26 or newer installation")
    _, app = max(candidates, key=lambda item: item[0])
    os.environ["DEVELOPER_DIR"] = str(app / "Contents/Developer")
    print("Selected " + app.name, flush=True)


def run(name, command, cwd=ROOT):
    print(f"Starting {name}", flush=True)
    ARTIFACTS.mkdir(exist_ok=True)
    with (ARTIFACTS / f"{name}.log").open("w", encoding="utf-8") as log:
        process = subprocess.Popen(command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            print(line, end="", flush=True)
            log.write(line)
        code = process.wait()
    if code: raise RuntimeError(f"{name} failed with exit code {code}")


def simulator(platform, name):
    result = json.loads(subprocess.check_output(["xcrun", "simctl", "list", "devices", "available", "--json"]))
    candidates = [(runtime, d) for runtime, devices in result["devices"].items() if platform in runtime for d in devices if name in d["name"]]
    if not candidates: raise RuntimeError(f"No {platform} {name} simulator is installed")
    runtime, device = max(candidates, key=lambda x: (tuple(map(int, re.findall(r"\d+", x[0]))), "Ultra" in x[1]["name"], "Pro Max" in x[1]["name"], x[1]["name"]))
    print(f"Testing {device['name']} on {runtime}", flush=True)
    return device["udid"]


def verify_archive(path, signed=False):
    phone = path / "Products/Applications/Galleonaire.app"
    watch = phone / "Watch/GalleonaireWatch.app"
    assert phone.is_dir() and watch.is_dir(), "Watch must be embedded in the iPhone app's Watch directory"
    info = plistlib.loads((phone / "Info.plist").read_bytes())
    watch_info = plistlib.loads((watch / "Info.plist").read_bytes())
    assert info["CFBundleIdentifier"] == "com.sidneytambin.galleonaire"
    assert watch_info["CFBundleIdentifier"] == "com.sidneytambin.galleonaire.watchkitapp"
    assert info["CFBundleDisplayName"] == watch_info["CFBundleDisplayName"] == "Galleonaire"
    assert watch_info["WKCompanionAppBundleIdentifier"] == info["CFBundleIdentifier"]
    assert watch_info["WKApplication"] is True
    assert info["CFBundleVersion"] == watch_info["CFBundleVersion"]
    assert info["CFBundleShortVersionString"] == watch_info["CFBundleShortVersionString"]
    for app in [phone, watch]:
        assert (app / "Assets.car").exists(), "Missing compiled icons"
        assert (app / "magical-library.wav").exists(), "Missing background music"
        assert any(app.rglob("questions.json")), "Missing question resource bundle"
        assert (app / "PrivacyInfo.xcprivacy").exists(), "Missing privacy manifest"
    (ARTIFACTS / "archive-verification.json").write_text(json.dumps({"phoneBundle": info["CFBundleIdentifier"], "watchBundle": watch_info["CFBundleIdentifier"], "version": info["CFBundleShortVersionString"], "build": info["CFBundleVersion"], "watchEmbedded": True, "signed": signed}, indent=2))


def test_ui(name, scheme, platform, device_name, base):
    result = ARTIFACTS / f"{name}.xcresult"
    device = simulator(platform, device_name)
    subprocess.run(["xcrun", "simctl", "boot", device], capture_output=True)
    run(name.lower() + "-boot", ["xcrun", "simctl", "bootstatus", device, "-b"])
    try:
        run(name.lower() + "-ui-tests", base + ["-scheme", scheme, "-destination", "id=" + device, "-parallel-testing-enabled", "NO", "-resultBundlePath", str(result), "test"])
    finally:
        if result.exists():
            for label, command in [
                ("summary", ["get", "test-results", "summary", "--path", str(result)]),
                ("attachments", ["export", "attachments", "--path", str(result), "--output-path", str(ARTIFACTS / (name + "-attachments"))]),
            ]:
                try: run(name.lower() + "-" + label, ["xcrun", "xcresulttool"] + command)
                except RuntimeError as error: print(str(error), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=["all", "unit", "phone", "watch", "archive"], default="all")
    args = parser.parse_args()
    select_xcode()
    run("xcode-version", ["xcodebuild", "-version"])
    if args.stage in ["all", "unit"]: run("core-tests", ["swift", "test", "--package-path", "Apple"])
    if args.stage == "unit": raise SystemExit(0)
    run("generate-project", ["xcodegen", "generate", "--spec", "Apple/project.yml", "--project", "Apple"])
    base = ["xcodebuild", "-project", "Apple/Galleonaire.xcodeproj", "CODE_SIGNING_ALLOWED=NO"]
    failures = []
    for stage, name, scheme, platform, device in [
        ("phone", "iPhone", "Galleonaire", "iOS", "iPhone"),
        ("watch", "Watch", "GalleonaireWatch", "watchOS", "Apple Watch"),
    ]:
        if args.stage in ["all", stage]:
            try: test_ui(name, scheme, platform, device, base)
            except RuntimeError as error: failures.append(str(error))
    if args.stage in ["all", "archive"]:
        path = ARTIFACTS / "Galleonaire.xcarchive"
        try:
            run("release-archive", base + ["-scheme", "Galleonaire", "-configuration", "Release", "-destination", "generic/platform=iOS", "-archivePath", str(path), "archive"])
            verify_archive(path)
        except (RuntimeError, AssertionError) as error: failures.append(str(error))
    if failures: raise SystemExit("\n".join(failures))
