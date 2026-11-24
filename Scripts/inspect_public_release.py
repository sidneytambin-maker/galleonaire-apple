"""Read only the app/version metadata needed for Galleonaire's public update."""
import base64
import json
import os
from apple_accounts import Apple

apple = Apple(base64.b64decode(os.environ['APP_STORE_CONNECT_KEY_BASE64']),
              os.environ['APP_STORE_CONNECT_KEY_ID'], os.environ['APP_STORE_CONNECT_ISSUER_ID'])
app = apple.request('GET', 'apps/6811170867')['data']
assert app['attributes']['bundleId'] == 'com.sidneytambin.galleonaire'
versions = apple.request('GET', 'apps/6811170867/appStoreVersions?limit=20')['data']
result = {'app': app['id'], 'versions': []}
for version in versions:
    entry = {'id': version['id'], 'attributes': version['attributes']}
    entry['localizations'] = apple.request('GET', 'appStoreVersions/' + version['id'] + '/appStoreVersionLocalizations')['data']
    entry['build'] = apple.request('GET', 'appStoreVersions/' + version['id'] + '/build')['data']
    result['versions'].append(entry)
result['submissions'] = apple.request('GET', 'apps/6811170867/reviewSubmissions')['data']
print(json.dumps(result, indent=2))
