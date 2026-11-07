"""Reuse one test build for every iPhone/Watch model supported by the public runtime."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
from ci import ARTIFACTS, ROOT, ensure_runtimes, run, select_xcode
from reuse_validation import reused_models


def model_plan(runtimes, prefix):
    # Hardware-specific runtimes (for example iPhone Duo) supplement the general runtime.
    models = {}
    for runtime in sorted(runtimes, key=lambda r: len(r.get("supportedDeviceTypes", [])), reverse=True):
        for model in runtime.get("supportedDeviceTypes", []):
            if model["name"].startswith(prefix):
                models.setdefault(model["identifier"], (runtime, model))
    if not models: raise RuntimeError("The runtime catalogues did not expose any supported models")
    return sorted(models.values(), key=lambda pair: pair[1]["name"])


def assigned_models(models, index, count):
    if count < 1 or not 0 <= index < count or count > len(models):
        raise ValueError("Every model shard must be valid and nonempty")
    return models[index::count]


def verify(platform, shard_index=0, shard_count=1):
    select_xcode()
    run("xcode-version", ["xcodebuild", "-version"])
    os_name = "iOS" if platform == "phone-models" else "watchOS"
    prefix = "iPhone" if os_name == "iOS" else "Apple Watch"
    scheme = "Galleonaire" if os_name == "iOS" else "GalleonaireWatch"
    test_class = "GalleonaireUITests" if os_name == "iOS" else "GalleonaireWatchUITests"
    runtimes = ensure_runtimes(os_name)
    all_models = model_plan(runtimes, prefix)
    models = assigned_models(all_models, shard_index, shard_count)
    report = {"platform": os_name, "runtime": "27.2",
              "shardIndex": shard_index, "shardCount": shard_count,
              "allSupportedModels": [d["name"] for _, d in all_models],
              "expectedModels": [d["name"] for _, d in models], "complete": False, "models": []}
    ARTIFACTS.mkdir(exist_ok=True)
    verified_models = reused_models(platform, shard_index, shard_count)
    run("generate-project", ["xcodegen", "generate", "--spec", "Apple/project.yml", "--project", "Apple"])
    base = ["xcodebuild", "-project", "Apple/Galleonaire.xcodeproj", "-scheme", scheme,
            "CODE_SIGNING_ALLOWED=NO", "-derivedDataPath", str(ROOT / ".model-build"), "-parallel-testing-enabled", "NO"]
    run("model-test-build", base + ["-destination", "generic/platform=" + os_name + " Simulator", "build-for-testing"])
    for runtime, model in models:
        previous = verified_models.get(model["identifier"])
        if previous and previous["model"] == model["name"] and previous["runtime"] == runtime["identifier"] and previous["runtimeBuild"] == runtime["buildversion"]:
            report["models"].append(previous)
            report["complete"] = len(report["models"]) == len(models) and all(m["passed"] for m in report["models"])
            (ARTIFACTS / "model-compatibility.json").write_text(json.dumps(report, indent=2) + "\n")
            print("Reused successful model check: " + model["name"], flush=True)
            continue
        label = re.sub(r"[^A-Za-z0-9]+", "-", model["name"]).strip("-")
        record = {"model": model["name"], "deviceType": model["identifier"], "runtime": runtime["identifier"],
                  "runtimeBuild": runtime["buildversion"], "passed": False}
        report["models"].append(record)
        device = subprocess.check_output(["xcrun", "simctl", "create", "Galleonaire " + model["name"], model["identifier"], runtime["identifier"]], text=True).strip()
        try:
            subprocess.run(["xcrun", "simctl", "boot", device], check=True, timeout=60)
            if model["name"] == "iPhone Duo":
                hub = Path(os.environ["DEVELOPER_DIR"]).parent / "Applications/DeviceHub.app"
                subprocess.run(["open", "-a", str(hub), "--args", "-CurrentDeviceUDID", device], check=True, timeout=45)
            subprocess.run(["xcrun", "simctl", "bootstatus", device, "-b"], check=True, timeout=300)
            run(label + "-smoke", base + ["-destination", "id=" + device, "-resultBundlePath", str(ARTIFACTS / (label + ".xcresult")),
                "-only-testing:" + test_class + "/" + test_class + "/testSupportedModelClassicExamAndStatisticsSmoke", "test-without-building"])
            summary = json.loads(subprocess.check_output(["xcrun", "xcresulttool", "get", "test-results", "summary", "--path", str(ARTIFACTS / (label + ".xcresult"))]))
            if summary.get("totalTestCount") != 1 or summary.get("passedTests") != 1:
                raise RuntimeError("The model smoke test did not execute and pass exactly once")
            record["passed"] = True
        except (RuntimeError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
            record["error"] = str(error)
        finally:
            report["complete"] = len(report["models"]) == len(models) and all(m["passed"] for m in report["models"])
            (ARTIFACTS / "model-compatibility.json").write_text(json.dumps(report, indent=2) + "\n")
            for action in ["shutdown", "delete"]:
                try: subprocess.run(["xcrun", "simctl", action, device], capture_output=True, timeout=30)
                except subprocess.TimeoutExpired: print(f"Simulator {action} timed out for {device}", flush=True)
            result = ARTIFACTS / (label + ".xcresult")
            if result.exists():
                run(label + "-attachments", ["xcrun", "xcresulttool", "export", "attachments", "--path", str(result), "--output-path", str(ARTIFACTS / (label + "-attachments"))])
        if not record["passed"]: break
    print(json.dumps(report, indent=2), flush=True)
    if not report["complete"]: raise RuntimeError("One or more model smoke checks failed; see model-compatibility.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", choices=["phone-models", "watch-models"], required=True)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    args = parser.parse_args()
    verify(args.platform, args.shard_index, args.shard_count)
