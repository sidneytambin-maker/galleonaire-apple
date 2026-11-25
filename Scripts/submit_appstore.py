"""Submit the exact validated public build; never distribute it to beta groups."""
import argparse
import base64
import json
import os
import time
from datetime import datetime, timezone

from apple_accounts import Apple
from beta_metadata import ROOT, native_gate
from complete_testflight import wait_for_build

ACCEPTED = {'WAITING_FOR_REVIEW', 'IN_REVIEW', 'COMPLETE'}


def resource(kind, identifier):
    return {'data': {'type': kind, 'id': identifier}}


def validate_metadata(metadata, request):
    if request.get('channel') != 'app-store' or request.get('version') != metadata.get('version'):
        raise ValueError('Explicit matching public release request required')
    if metadata.get('app') != '6811170867' or metadata.get('locale') != 'en-GB':
        raise ValueError('Unexpected app or locale')
    for field, maximum in [('description', 4000), ('whatsNew', 4000), ('promotionalText', 170), ('reviewNotes', 4000)]:
        value = metadata.get(field)
        if not isinstance(value, str) or not 20 <= len(value) <= maximum:
            raise ValueError('Invalid public metadata: ' + field)
    if '1,500' not in metadata['whatsNew']:
        raise ValueError('Question total missing from public release notes')


def patch(apple, kind, identifier, attributes):
    apple.request('PATCH', kind + '/' + identifier, {'data': {
        'type': kind, 'id': identifier, 'attributes': attributes}})


def verify_submission(apple, version_id, build_id, version, submission_id):
    saved = apple.request('GET', 'appStoreVersions/' + version_id)['data']
    linked = apple.request('GET', 'appStoreVersions/' + version_id + '/build')['data']
    review = apple.request('GET', 'reviewSubmissions/' + submission_id)['data']
    items = apple.request('GET', 'reviewSubmissions/' + submission_id + '/items')['data']
    if saved['attributes']['versionString'] != version or not linked or linked['id'] != build_id:
        raise ValueError('The submitted version or build does not match the validated release')
    if not any(i.get('relationships', {}).get('appStoreVersion', {}).get('data', {}).get('id') == version_id for i in items):
        raise ValueError('The public version is not attached to this review submission')
    state = review['attributes']['state']
    if state not in ACCEPTED:
        raise ValueError('Public review submission is not submitted: ' + state)
    return {'reviewSubmission': submission_id, 'reviewState': state,
            'appStoreVersion': version_id, 'versionState': saved['attributes'].get('appStoreState'),
            'submittedForPublicReview': True, 'verifiedAt': datetime.now(timezone.utc).isoformat()}


def submit(run_id):
    run = native_gate(run_id)
    request = json.loads((ROOT / 'Docs/Release-Request.json').read_text())
    metadata = json.loads((ROOT / 'Docs/AppStore-Metadata.json').read_text())
    validate_metadata(metadata, request)
    key = base64.b64decode(os.environ['APP_STORE_CONNECT_KEY_BASE64'], validate=True)
    def client():
        return Apple(key, os.environ['APP_STORE_CONNECT_KEY_ID'], os.environ['APP_STORE_CONNECT_ISSUER_ID'])
    app_id, build_id = wait_for_build(client, run['run_number'], metadata['version'], time.monotonic() + 1800)
    if app_id != metadata['app']:
        raise ValueError('Unexpected app identity')
    apple = client()
    versions = apple.request('GET', 'apps/' + app_id + '/appStoreVersions?limit=100')['data']
    target = next((v for v in versions if v['attributes']['versionString'] == metadata['version'] and v['attributes']['platform'] == 'IOS'), None)
    previous = next(v for v in versions if v['attributes'].get('appStoreState') == 'READY_FOR_SALE' and v['attributes']['platform'] == 'IOS')
    active = [v for v in versions if v['attributes'].get('appStoreState') not in {'READY_FOR_SALE', 'REMOVED_FROM_SALE', 'REPLACED_WITH_NEW_VERSION'} and v['attributes']['platform'] == 'IOS']
    if any(v['id'] != (target or {}).get('id') for v in active):
        raise ValueError('Another public version is already being prepared')
    if not target:
        target = apple.request('POST', 'appStoreVersions', {'data': {
            'type': 'appStoreVersions', 'attributes': {'platform': 'IOS', 'versionString': metadata['version'],
                'copyright': previous['attributes']['copyright'], 'releaseType': 'AFTER_APPROVAL'},
            'relationships': {'app': resource('apps', app_id)}}})['data']
    version_id = target['id']
    base = 'appStoreVersions/' + version_id
    submissions = apple.request('GET', 'apps/' + app_id + '/reviewSubmissions?limit=100')['data']
    submission = None
    for entry in submissions:
        items = apple.request('GET', 'reviewSubmissions/' + entry['id'] + '/items')['data']
        belongs = any(i.get('relationships', {}).get('appStoreVersion', {}).get('data', {}).get('id') == version_id for i in items)
        if belongs:
            submission = entry
            if entry['attributes']['state'] in ACCEPTED:
                result = verify_submission(apple, version_id, build_id, metadata['version'], entry['id'])
                return report(result, run, app_id, build_id, metadata)
        elif entry['attributes']['state'] not in {'COMPLETE', 'CANCELED'}:
            raise ValueError('Another unfinished App Review submission exists')
    if target['attributes']['appStoreState'] not in {'PREPARE_FOR_SUBMISSION', 'DEVELOPER_REJECTED', 'REJECTED', 'METADATA_REJECTED'}:
        raise ValueError('Public version is not editable: ' + target['attributes']['appStoreState'])
    patch(apple, 'appStoreVersions', version_id, {'releaseType': 'AFTER_APPROVAL'})
    apple.request('PATCH', base + '/relationships/build', resource('builds', build_id))
    localizations = apple.request('GET', base + '/appStoreVersionLocalizations')['data']
    locale = next((loc for loc in localizations if loc['attributes']['locale'] == metadata['locale']), None)
    attributes = {k: metadata[k] for k in ['description', 'whatsNew', 'promotionalText', 'supportUrl', 'keywords']}
    if locale:
        patch(apple, 'appStoreVersionLocalizations', locale['id'], attributes)
    else:
        locale = apple.request('POST', 'appStoreVersionLocalizations', {'data': {
            'type': 'appStoreVersionLocalizations', 'attributes': {'locale': metadata['locale'], **attributes},
            'relationships': {'appStoreVersion': resource('appStoreVersions', version_id)}}})['data']
    saved = apple.request('GET', 'appStoreVersionLocalizations/' + locale['id'])['data']['attributes']
    if any(saved.get(k) != value for k, value in attributes.items()):
        raise ValueError('Apple did not retain public metadata')
    sets = apple.request('GET', 'appStoreVersionLocalizations/' + locale['id'] + '/appScreenshotSets')['data']
    screenshots = sum(len(apple.request('GET', 'appScreenshotSets/' + s['id'] + '/appScreenshots')['data']) for s in sets)
    if not screenshots:
        raise ValueError('Public version needs its App Store screenshots before submission')
    detail = apple.request('GET', base + '/appStoreReviewDetail')['data']
    old_detail = apple.request('GET', 'appStoreVersions/' + previous['id'] + '/appStoreReviewDetail')['data']
    # Keep verified owner contact information within Apple/cloud memory, never in logs.
    fields = {k: old_detail['attributes'][k] for k in ['contactFirstName', 'contactLastName', 'contactPhone', 'contactEmail']}
    fields.update(demoAccountRequired=False, notes=metadata['reviewNotes'])
    if detail:
        patch(apple, 'appStoreReviewDetails', detail['id'], fields)
    else:
        detail = apple.request('POST', 'appStoreReviewDetails', {'data': {'type': 'appStoreReviewDetails',
            'attributes': fields, 'relationships': {'appStoreVersion': resource('appStoreVersions', version_id)}}})['data']
    saved_detail = apple.request('GET', base + '/appStoreReviewDetail')['data']['attributes']
    if any(saved_detail.get(k) != v for k, v in fields.items()):
        raise ValueError('Apple did not retain review information')
    if not submission:
        submission = apple.request('POST', 'reviewSubmissions', {'data': {'type': 'reviewSubmissions',
            'attributes': {'platform': 'IOS'}, 'relationships': {'app': resource('apps', app_id)}}})['data']
    sid = submission['id']
    items = apple.request('GET', 'reviewSubmissions/' + sid + '/items')['data']
    if not any(i.get('relationships', {}).get('appStoreVersion', {}).get('data', {}).get('id') == version_id for i in items):
        apple.request('POST', 'reviewSubmissionItems', {'data': {'type': 'reviewSubmissionItems', 'relationships': {
            'reviewSubmission': resource('reviewSubmissions', sid), 'appStoreVersion': resource('appStoreVersions', version_id)}}})
    patch(apple, 'reviewSubmissions', sid, {'submitted': True})
    result = verify_submission(apple, version_id, build_id, metadata['version'], sid)
    result.update(metadataVerified=True, reviewInformationVerified=True, screenshotCount=screenshots, releaseType='AFTER_APPROVAL')
    return report(result, run, app_id, build_id, metadata)


def report(result, run, app_id, build_id, metadata):
    result.update(app=app_id, build=build_id, buildNumber=str(run['run_number']), version=metadata['version'],
                  releaseCommit=run['head_sha'], releaseRunId=str(run['id']), channel='APP_STORE')
    destination = ROOT / 'Artifacts/appstore-submission-status.json'
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--verified-run', required=True)
    submit(parser.parse_args().verified_run)
