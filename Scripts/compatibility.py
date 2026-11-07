"""Reuse one test build for every iPhone/Watch model supported by the public runtime."""
import argparse
import json
import re
import subprocess
from ci import ARTIFACTS, ROOT, ensure_runtime, run, select_xcode


def verify(platform):
    select_xcode()
    run("xcode-version", ["xcodebuild", "-version"])
    os_name = "iOS" if platform == "phone-models" else "watchOS"
    prefix = "iPhone" if os_name == "iOS" else "Apple Watch"
    scheme = "Galleonaire" if os_name == "iOS" else "GalleonaireWatch"
    test_class = "GalleonaireUITests" if os_name == "iOS" else "GalleonaireWatchUITests"
    runtime = ensure_runtime(os_name)
    models = [d for d in runtime["supportedDeviceTypes"] if d["name"].startswith(prefix)]
    if not models: raise RuntimeError("The runtime did not expose any supported models")
    report = {"platform": os_name, "runtime": runtime["version"], "runtimeBuild": runtime["buildversion"],
              "expectedModels": [d["name"] for d in models], "complete": False, "models": []}
    ARTIFACTS.mkdir(exist_ok=True)
    run("generate-project", ["xcodegen", "generate", "--spec", "Apple/project.yml", "--project", "Apple"])
    base = ["xcodebuild", "-project", "Apple/Galleonaire.xcodeproj", "-scheme", scheme,
            "CODE_SIGNING_ALLOWED=NO", "-derivedDataPath", str(ROOT / ".model-build"), "-parallel-testing-enabled", "NO"]
    run("model-test-build", base + ["-destination", "generic/platform=" + os_name + " Simulator", "build-for-testing"])
    for model in models:
        label = re.sub(r"[^A-Za-z0-9]+", "-", model["name"]).strip("-")
        record = {"model": model["name"], "deviceType": model["identifier"], "passed": False}
        report["models"].append(record)
        device = subprocess.check_output(["xcrun", "simctl", "create", "Galleonaire " + model["name"], model["identifier"], runtime["identifier"]], text=True).strip()
        try:
            subprocess.run(["xcrun", "simctl", "boot", device], check=True)
            run(label + "-boot", ["xcrun", "simctl", "bootstatus", device, "-b"])
            run(label + "-smoke", base + ["-destination", "id=" + device, "-resultBundlePath", str(ARTIFACTS / (label + ".xcresult")),
                "-only-testing:" + test_class + "/" + test_class + "/testSupportedModelClassicExamAndStatisticsSmoke", "test-without-building"])
            summary = json.loads(subprocess.check_output(["xcrun", "xcresulttool", "get", "test-results", "summary", "--path", str(ARTIFACTS / (label + ".xcresult"))]))
            if summary.get("totalTestCount") != 1 or summary.get("passedTests") != 1:
                raise RuntimeError("The model smoke test did not execute and pass exactly once")
            record["passed"] = True
        except (RuntimeError, subprocess.CalledProcessError) as error:
            record["error"] = str(error)
        finally:
            subprocess.run(["xcrun", "simctl", "shutdown", device], capture_output=True)
            subprocess.run(["xcrun", "simctl", "delete", device], capture_output=True)
            report["complete"] = len(report["models"]) == len(models) and all(m["passed"] for m in report["models"])
            (ARTIFACTS / "model-compatibility.json").write_text(json.dumps(report, indent=2) + "\n")
            result = ARTIFACTS / (label + ".xcresult")
            if result.exists():
                run(label + "-attachments", ["xcrun", "xcresulttool", "export", "attachments", "--path", str(result), "--output-path", str(ARTIFACTS / (label + "-attachments"))])
        if not record["passed"]: break
    if not all(m["passed"] for m in report["models"]): raise RuntimeError("One or more model smoke checks failed; see model-compatibility.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", choices=["phone-models", "watch-models"], required=True)
    verify(parser.parse_args().platform)
