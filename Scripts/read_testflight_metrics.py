"""Read aggregate Galleonaire metrics without publishing tester identities."""
import base64
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import os
from urllib.parse import urlencode

from apple_accounts import Apple
from beta_metadata import ROOT, resolve_app
from diagnose_testflight_access import pages


def main():
    apple = Apple(base64.b64decode(os.environ["APP_STORE_CONNECT_KEY_BASE64"], validate=True),
                  os.environ["APP_STORE_CONNECT_KEY_ID"], os.environ["APP_STORE_CONNECT_ISSUER_ID"])
    app = resolve_app(apple)
    report = {"app": app, "readAt": datetime.now(timezone.utc).isoformat()}
    builds = pages(apple, "builds?" + urlencode({"filter[app]": app, "limit": 200}))

    def read_build(build):
        attrs = build["attributes"]
        metrics = pages(apple, "builds/" + build["id"] + "/metrics/betaBuildUsages")
        version = apple.request("GET", "builds/" + build["id"] + "/preReleaseVersion")["data"]["attributes"]["version"]
        detail = apple.request("GET", "builds/" + build["id"] + "/buildBetaDetail")["data"]["attributes"]
        return {"version": version, "build": attrs["version"], "expired": attrs.get("expired"),
                "processingState": attrs.get("processingState"),
                "internalBuildState": detail.get("internalBuildState"),
                "externalBuildState": detail.get("externalBuildState"),
                "dataPoints": [p for item in metrics for p in item.get("dataPoints", [])]}

    with ThreadPoolExecutor(max_workers=6) as pool:
        report["builds"] = list(pool.map(read_build, builds))
    testers = pages(apple, "apps/" + app + "/betaTesters?limit=200")
    unique = {tester["id"]: tester for tester in testers}
    report["currentUniqueTesterCount"] = len(unique)
    report["currentTesterStates"] = dict(Counter(t["attributes"].get("state") for t in unique.values()))
    report["appStoreVersions"] = [{"version": v["attributes"].get("versionString"),
                                    "state": v["attributes"].get("appStoreState")}
        for v in pages(apple, "apps/" + app + "/appStoreVersions?limit=200")]
    try:
        requests = pages(apple, "apps/" + app + "/analyticsReportRequests?limit=200")
        inventory = []
        for request in requests:
            for item in pages(apple, "analyticsReportRequests/" + request["id"] + "/reports?limit=200"):
                inventory.append({"id": item["id"], "name": item["attributes"].get("name"),
                                  "category": item["attributes"].get("category")})
        report["existingAnalyticsReports"] = inventory
        report["analyticsRequestCount"] = len(requests)
    except RuntimeError as error:
        report["analyticsReportErrors"] = [{"status": e.get("status"), "code": e.get("code")}
                                            for e in json.loads(str(error))]
    output = ROOT / "Artifacts/testflight-latest-metrics.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
