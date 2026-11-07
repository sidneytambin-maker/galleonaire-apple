"""Reuse successful same-product checks; failed or changed-product checks run again."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REPO = "sidneytambin-maker/galleonaire-apple"


def eligible(run, jobs, stage, shard, shards, product_tree, baseline_tree, now, allow_partial=False):
    if run.get("path") != ".github/workflows/testflight.yml" or run.get("head_branch") != "main":
        return None
    age = (now - datetime.fromisoformat(run["created_at"].replace("Z", "+00:00"))).total_seconds()
    if not 0 <= age <= 86400 or product_tree != baseline_tree:
        return None
    matches = [job for job in jobs if job["name"] == f"validation ({stage}, {shard}, {shards})"]
    conclusions = {"success", "failure"} if allow_partial else {"success"}
    if len(matches) != 1 or matches[0]["status"] != "completed" or matches[0]["conclusion"] not in conclusions:
        return None
    return matches[0]


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def api(path):
    return json.loads(subprocess.check_output(["gh", "api", f"repos/{REPO}/{path}"], text=True))


def reviewed_test_changes(changes, corrections):
    """Only an explicitly reviewed, exact test-only blob transition may differ."""
    allowed = {item["path"]: item for item in corrections}
    return all(path.startswith(("Apple/UITests/", "Apple/WatchUITests/")) and path in allowed
               and pair == (allowed[path]["baselineBlob"], allowed[path]["currentBlob"])
               for path, pair in changes.items())


def baseline_context(stage, shard, shards, allow_partial=False):
    request = json.loads((ROOT / "Docs/Release-Request.json").read_text())
    baseline = request.get("reuseValidationRun")
    if not isinstance(baseline, int) or stage in request.get("recheckValidationStages", []):
        return False
    # Generated resources must still match the committed, tested product.
    if git("status", "--porcelain", "--", "Apple"):
        return False
    run = api(f"actions/runs/{baseline}")
    jobs = api(f"actions/runs/{baseline}/jobs?per_page=100")["jobs"]
    product_tree = git("rev-parse", "HEAD:Apple")
    baseline_tree = git("rev-parse", run["head_sha"] + ":Apple")
    paths = git("diff", "--name-only", run["head_sha"], "HEAD", "--", "Apple").splitlines()
    corrections = request.get("verifiedTestHarnessCorrections", [])
    if any(path not in {item["path"] for item in corrections} for path in paths):
        return False
    changes = {path: (git("rev-parse", run["head_sha"] + ":" + path), git("rev-parse", "HEAD:" + path)) for path in paths}
    if not reviewed_test_changes(changes, corrections):
        return False
    # The app, resources and original assertions are unchanged. Corrections are
    # exact reviewed test-locator changes, recorded alongside the reused evidence.
    comparable_tree = baseline_tree if changes else product_tree
    job = eligible(run, jobs, stage, shard, shards, comparable_tree, baseline_tree,
                   datetime.now(timezone.utc), allow_partial=allow_partial)
    if not job:
        return False
    report = {"reused": True, "stage": stage, "shard": shard, "shards": shards,
              "productTree": product_tree, "sourceRun": baseline, "sourceCommit": run["head_sha"],
              "sourceJob": job["id"], "sourceJobURL": job["html_url"], "conclusion": job["conclusion"],
              "baselineAppleTree": baseline_tree, "testHarnessCorrections": corrections if changes else [],
              "verifiedAt": datetime.now(timezone.utc).isoformat()}
    return report


def reuse(stage, shard, shards):
    report = baseline_context(stage, shard, shards)
    if not report:
        return False
    output = ROOT / "Artifacts"
    output.mkdir(exist_ok=True)
    (output / "validation-reuse.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report), flush=True)
    return True


def parse_model_report(log):
    clean = re.sub(r"^\d{4}-\d\d-\d\dT\S+Z ", "", log, flags=re.MULTILINE)
    starts = list(re.finditer(r'\{\r?\n\s*"platform":', clean))
    if not starts:
        raise ValueError("No completed model report was found in the source log")
    return json.JSONDecoder().raw_decode(clean[starts[-1].start():])[0]


def reused_models(stage, shard, shards):
    source = baseline_context(stage, shard, shards, allow_partial=True)
    if not source:
        return {}
    log = subprocess.check_output(["gh", "api", f"repos/{REPO}/actions/jobs/{source['sourceJob']}/logs"], text=True)
    report = parse_model_report(log)
    if report["shardIndex"] != shard or report["shardCount"] != shards:
        raise ValueError("The source model group does not match this group")
    output = ROOT / "Artifacts"
    output.mkdir(exist_ok=True)
    (output / "partial-model-baseline.json").write_text(json.dumps({"source": source, "report": report}, indent=2))
    return {model["deviceType"]: {**model, "reusedFromRun": source["sourceRun"], "reusedFromJob": source["sourceJob"]}
            for model in report["models"] if model.get("passed") is True}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True)
    parser.add_argument("--shard", type=int, required=True)
    parser.add_argument("--shards", type=int, required=True)
    args = parser.parse_args()
    raise SystemExit(0 if reuse(args.stage, args.shard, args.shards) else 1)
