"""Create a fail-closed main-only environment. Does not read or upload secrets."""
import json
import shutil
import subprocess

REPOSITORY = "sidneytambin-maker/galleonaire-apple"
ENVIRONMENT = "testflight"


def api(method, endpoint, body=None):
    command = [shutil.which("gh") or r"C:\Program Files\GitHub CLI\gh.exe", "api", "--method", method, endpoint]
    if body is not None: command += ["--input", "-"]
    result = subprocess.run(command, input=json.dumps(body) if body is not None else None, text=True, capture_output=True)
    if result.returncode: raise RuntimeError(result.stderr.strip())
    return json.loads(result.stdout) if result.stdout.strip() else None


def main():
    path = f"repos/{REPOSITORY}/environments/{ENVIRONMENT}"
    environments = api("GET", f"repos/{REPOSITORY}/environments")
    existing = next((e for e in environments["environments"] if e["name"] == ENVIRONMENT), None)
    if existing:
        secrets = api("GET", path + "/secrets")
        if secrets["total_count"]:
            raise RuntimeError("Environment already contains secrets; refusing to change its policy automatically")
    # GitHub selected-branch policy admits only matching names, not every unprotected branch.
    # There are no secrets or signing jobs here during configuration.
    api("PUT", path, {"deployment_branch_policy": {"protected_branches": False, "custom_branch_policies": True}})
    policies = api("GET", path + "/deployment-branch-policies")
    if any(p["name"] != "main" or p["type"] != "branch" for p in policies["branch_policies"]):
        raise RuntimeError("Unexpected branch rule: no credentials may be added")
    if not policies["branch_policies"]:
        api("POST", path + "/deployment-branch-policies", {"name": "main", "type": "branch"})
    environment = api("GET", path)
    policies = api("GET", path + "/deployment-branch-policies")
    assert environment["deployment_branch_policy"] == {"protected_branches": False, "custom_branch_policies": True}
    assert [(p["name"], p["type"]) for p in policies["branch_policies"]] == [("main", "branch")]
    print("Verified: testflight accepts only the main branch; no credentials uploaded.")


if __name__ == "__main__": main()
