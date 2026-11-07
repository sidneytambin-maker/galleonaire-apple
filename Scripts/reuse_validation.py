"""Reuse successful same-product checks; failed or changed-product checks run again."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REPO = "sidneytambin-maker/galleonaire-apple"


def eligible(run, jobs, stage, shard, shards, product_tree, baseline_tree, now):
    if run.get("path") != ".github/workflows/testflight.yml" or run.get("head_branch") != "main":
        return None
    age = (now - datetime.fromisoformat(run["created_at"].replace("Z", "+00:00"))).total_seconds()
    if not 0 <= age <= 86400 or product_tree != baseline_tree:
        return None
    matches = [job for job in jobs if job["name"] == f"validation ({stage}, {shard}, {shards})"]
    if len(matches) != 1 or matches[0]["status"] != "completed" or matches[0]["conclusion"] != "success":
        return None
    return matches[0]


def reuse(stage, shard, shards):
    request = json.loads((ROOT / "Docs/Release-Request.json").read_text())
    baseline = request.get("reuseValidationRun")
    if not isinstance(baseline, int) or stage in request.get("recheckValidationStages", []):
        return False
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
    def api(path):
        return json.loads(subprocess.check_output(["gh", "api", f"repos/{REPO}/{path}"], text=True))
    # Generated resources must still match the committed, tested product.
    if git("status", "--porcelain", "--", "Apple"):
        return False
    run = api(f"actions/runs/{baseline}")
    jobs = api(f"actions/runs/{baseline}/jobs?per_page=100")["jobs"]
    product_tree = git("rev-parse", "HEAD:Apple")
    baseline_tree = git("rev-parse", run["head_sha"] + ":Apple")
    job = eligible(run, jobs, stage, shard, shards, product_tree, baseline_tree, datetime.now(timezone.utc))
    if not job:
        return False
    report = {"reused": True, "stage": stage, "shard": shard, "shards": shards,
              "productTree": product_tree, "sourceRun": baseline, "sourceCommit": run["head_sha"],
              "sourceJob": job["id"], "sourceJobURL": job["html_url"], "conclusion": job["conclusion"],
              "verifiedAt": datetime.now(timezone.utc).isoformat()}
    output = ROOT / "Artifacts"
    output.mkdir(exist_ok=True)
    (output / "validation-reuse.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report), flush=True)
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True)
    parser.add_argument("--shard", type=int, required=True)
    parser.add_argument("--shards", type=int, required=True)
    args = parser.parse_args()
    raise SystemExit(0 if reuse(args.stage, args.shard, args.shards) else 1)
