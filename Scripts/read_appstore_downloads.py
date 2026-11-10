"""Read App Store download reports only; never query TestFlight metrics."""
import base64
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import csv
from datetime import datetime, timezone
import gzip
import io
import json
import os
from urllib.request import urlopen

from apple_accounts import Apple
from beta_metadata import ROOT, resolve_app
from diagnose_testflight_access import pages


def main():
    apple = Apple(base64.b64decode(os.environ["APP_STORE_CONNECT_KEY_BASE64"], validate=True),
                  os.environ["APP_STORE_CONNECT_KEY_ID"], os.environ["APP_STORE_CONNECT_ISSUER_ID"])
    app = resolve_app(apple)
    result = {"app": app, "readAt": datetime.now(timezone.utc).isoformat(), "source": "App Store Downloads"}
    result["appStoreVersions"] = [{"version": v["attributes"].get("versionString"),
                                    "state": v["attributes"].get("appStoreState")}
        for v in pages(apple, "apps/" + app + "/appStoreVersions?limit=200")]
    requests = pages(apple, "apps/" + app + "/analyticsReportRequests?limit=200")
    result["requests"] = [{"id": r["id"], **r["attributes"]} for r in requests]
    reports = []
    for request in requests:
        for report in pages(apple, "analyticsReportRequests/" + request["id"] + "/reports?limit=200"):
            if report["attributes"].get("name") == "App Store Downloads":
                reports.append(report)
    result["downloadReportCount"] = len(reports)
    instances = []
    for report in reports:
        for instance in pages(apple, "analyticsReports/" + report["id"] + "/instances?filter%5Bgranularity%5D=DAILY&limit=200"):
            instances.append(instance)
    # Reports can contain revised historical dates. Keep only the newest processing
    # date's complete rows for each download day, without adding revisions twice.
    def read_instance(instance):
        rows = []
        for segment in pages(apple, "analyticsReportInstances/" + instance["id"] + "/segments?limit=200"):
            with urlopen(segment["attributes"]["url"], timeout=60) as response:
                data = response.read()
            if data[:2] == b"\x1f\x8b":
                data = gzip.decompress(data)
            rows.extend(csv.DictReader(io.StringIO(data.decode("utf-8-sig")), delimiter="\t"))
        return instance["attributes"], rows
    days = {}
    with ThreadPoolExecutor(max_workers=6) as pool:
        for attributes, rows in pool.map(read_instance, instances):
            by_day = defaultdict(list)
            for row in rows:
                identifier = row.get("App Apple Identifier", row.get("App Apple ID"))
                if identifier and str(identifier) != app:
                    raise ValueError("Report includes an unexpected app")
                day = row.get("Date", row.get("Download Date", row.get("Download Day")))
                if not day or "Counts" not in row or "Download Type" not in row or "Territory" not in row:
                    raise ValueError("Unrecognised App Store Downloads report columns: " + ", ".join(row))
                by_day[day].append(row)
            for day, values in by_day.items():
                processed = attributes["processingDate"]
                if day not in days or processed > days[day][0]:
                    days[day] = (processed, values)
    countries = defaultdict(lambda: defaultdict(int))
    for _, rows in days.values():
        for row in rows:
            countries[row["Territory"]][row["Download Type"]] += int(row["Counts"])
    result["dateFrom"] = min(days) if days else None
    result["dateThrough"] = max(days) if days else None
    result["reportedDayCount"] = len(days)
    result["byCountryAndDownloadType"] = {k: dict(v) for k, v in countries.items()}
    result["instancesRead"] = len(instances)
    result["available"] = bool(days)
    output = ROOT / "Artifacts/appstore-downloads.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
