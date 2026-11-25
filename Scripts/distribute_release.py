"""Route a validated upload to the explicitly requested Apple distribution channel."""
import argparse
import json
from pathlib import Path


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--verified-run', required=True)
    args = parser.parse_args()
    request = json.loads((Path(__file__).resolve().parents[1] / 'Docs/Release-Request.json').read_text())
    if request.get('channel') == 'app-store':
        from submit_appstore import submit
        submit(args.verified_run)
    elif request.get('channel', 'testflight') == 'testflight':
        from complete_testflight import complete
        complete(args.verified_run, review_wait_seconds=60)
    else:
        raise ValueError('Unknown release channel')
