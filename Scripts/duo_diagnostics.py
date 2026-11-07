"""Inspect the installed Apple simulator's supported dual-display controls."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from ci import ARTIFACTS, select_xcode

select_xcode()
ARTIFACTS.mkdir(exist_ok=True)

def inspect(name, args, timeout=45):
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)
        output = result.stdout + result.stderr
    except subprocess.TimeoutExpired as error:
        output = 'Timed out: ' + str(error) + '\n' + (error.stdout or b'').decode(errors='replace') + (error.stderr or b'').decode(errors='replace')
    (ARTIFACTS / (name + '.txt')).write_text(output)
    print(name + '\n' + output, flush=True)
    return output

inspect('xcode-version', ['xcodebuild', '-version'])
inspect('simctl-help', ['xcrun', 'simctl', 'help'])
inspect('simctl-io-help', ['xcrun', 'simctl', 'help', 'io'])
inspect('simctl-ui-help', ['xcrun', 'simctl', 'help', 'ui'])
inspect('coredevice-commands', ['xcrun', 'devicectl', 'help', 'device'])
if '--controls-only' in sys.argv:
    for command in ['simulate', 'settings', 'info', 'capture', 'appResize']:
        inspect('coredevice-' + command, ['xcrun', 'devicectl', 'help', 'device', command])
    sys.exit(0)
inspect('host-capabilities', ['sysctl', 'machdep.cpu.brand_string', 'kern.hv_support', 'hw.memsize'])
developer = Path(os.environ['DEVELOPER_DIR'])
paths = list(developer.glob('Platforms/iPhoneSimulator.platform/Developer/Library/Frameworks/XC*.framework/Headers/*.h'))
paths += list((developer / 'Applications').rglob('*.sdef'))
(ARTIFACTS / 'automation-interfaces.txt').write_text('\n'.join(str(p) + '\n' + p.read_text(errors='replace') for p in paths if p.suffix == '.sdef' or any(w in p.read_text(errors='replace').lower() for w in ['hinge', 'fold', 'pose', 'orientation'])))
apps = list(developer.parent.rglob('*DeviceHub*.app')) + list(developer.parent.rglob('Simulator.app'))
print('Simulator applications: ' + ', '.join(str(p) for p in apps), flush=True)
runtimes = json.loads(subprocess.check_output(['xcrun', 'simctl', 'list', 'runtimes', '--json']))['runtimes']
runtime, model = next((r, d) for r in runtimes if r.get('isAvailable') and r['version'] == '27.2' for d in r.get('supportedDeviceTypes', []) if d['name'] == 'iPhone Duo')
device = subprocess.check_output(['xcrun', 'simctl', 'create', 'Duo layout inspection', model['identifier'], runtime['identifier']], text=True).strip()
try:
    inspect('duo-boot', ['xcrun', 'simctl', 'boot', device])
    if apps: inspect('open-device-ui', ['open', '-a', str(apps[0]), '--args', '-CurrentDeviceUDID', device])
    inspect('duo-boot-status', ['xcrun', 'simctl', 'bootstatus', device, '-b'], 300)
    inspect('duo-displays', ['xcrun', 'simctl', 'io', device, 'enumerate'])
    inspect('duo-coredevice', ['xcrun', 'devicectl', 'list', 'devices'])
    inspect('duo-boot-errors', ['log', 'show', '--last', '5m', '--style', 'compact', '--predicate', 'eventMessage CONTAINS[c] "virtualization" OR (process CONTAINS[c] "Simulator" AND messageType == error)'])
    time.sleep(5)
    script = '''tell application "System Events"
set found to {}
repeat with proc in (application processes whose background only is false)
if name of proc is "Simulator" or name of proc is "Device Hub" or name of proc is "DeviceHub" then
set end of found to {name of proc, entire contents of proc}
end if
end repeat
return found
end tell'''
    inspect('device-hub-accessibility', ['osascript', '-e', script])
finally:
    inspect('duo-shutdown', ['xcrun', 'simctl', 'shutdown', device], 30)
    inspect('duo-delete', ['xcrun', 'simctl', 'delete', device], 30)
