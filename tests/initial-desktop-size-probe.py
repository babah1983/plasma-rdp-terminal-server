#!/usr/bin/env python3
"""Protocol-only probe on the disposable ALT VM; does not replace Windows App acceptance."""
import json
import os
from pathlib import Path
import pwd
import re
import secrets
import subprocess
import sys
import tempfile
import time

if os.geteuid() != 0:
    raise SystemExit('Run only as root inside the disposable test VM')
if Path('/tmp/.X11-unix/X99').exists() or Path('/tmp/.X99-lock').exists():
    raise SystemExit('X display :99 is already in use; do not disturb it')

account = sys.argv[1] if len(sys.argv) > 1 else 'native-a'
requested = sys.argv[2] if len(sys.argv) > 2 else '1000x700'
check_dpms = len(sys.argv) > 3 and sys.argv[3] == '--expect-dpms-wake'
assert len(sys.argv) <= 4 and (len(sys.argv) < 4 or check_dpms)
assert account in ('native-a', 'native-b')
assert re.fullmatch(r'[0-9]{3,4}x[0-9]{3,4}', requested)
width, height = map(int, requested.split('x'))
assert 200 <= width <= 2048 and 200 <= height <= 1536
uid = pwd.getpwnam(account).pw_uid
state = Path(pwd.getpwnam(account).pw_dir) / '.local/state/plasma-rdp'
password = (state / 'password').read_text().strip()
fingerprint = subprocess.check_output(['openssl', 'x509', '-in', str(state / 'cert.pem'),
                                       '-noout', '-fingerprint', '-sha256'], text=True)
fingerprint = fingerprint.strip().split('=')[-1].replace(':', '')
port = 3391 if account == 'native-a' else 3392
bus_env = ['runuser', '-u', account, '--', 'env', 'LANG=C.UTF-8',
           f'XDG_RUNTIME_DIR=/run/user/{uid}', f'DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{uid}/bus']

def geometry():
    info = subprocess.check_output(bus_env + ['qdbus-qt6', 'org.kde.KWin', '/KWin', 'supportInformation'], text=True)
    match = re.search(r'^Geometry: [^,]+,[^,]+,(\d+)x(\d+)$', info, re.M)
    return tuple(map(int, match.groups())) if match else None

def dpms():
    info = subprocess.check_output(bus_env + ['QT_QPA_PLATFORM=wayland', 'WAYLAND_DISPLAY=wayland-0',
                                               'kscreen-doctor', '--dpms', 'show'], text=True)
    match = re.fullmatch(r'dpms mode for screen Virtual-0: (on|off)\n?', info)
    if not match:
        raise RuntimeError('DPMS probe requires exactly the dedicated Virtual-0')
    return match[1]

def pid(name):
    return subprocess.check_output(['pgrep', '-u', account, '-x', name], text=True).strip()

before = {name: pid(name) for name in ('kate', 'kwin_wayland', 'krdpserver')}
initial = geometry()
initial_dpms = dpms() if check_dpms else None
if check_dpms and initial_dpms != 'off':
    raise SystemExit('Set the disposable virtual output DPMS off before this negative/positive probe')
for _ in range(100):
    if subprocess.check_output(['ss', '-H', '-lnt', 'sport', '=', f':{port}'], text=True).strip():
        break
    time.sleep(.1)
else:
    raise RuntimeError('RDP backend did not start listening')
with tempfile.TemporaryDirectory(prefix='rdp-initial-size-') as directory:
    directory = Path(directory)
    authority = directory / 'Xauthority'
    subprocess.run(['xauth', '-f', str(authority)], input=f'add :99 . {secrets.token_hex(16)}\n',
                   text=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    env = dict(os.environ, DISPLAY=':99', XAUTHORITY=str(authority))
    with (directory / 'xvfb.log').open('w') as xlog, (directory / 'client.log').open('w') as clog:
        xvfb = subprocess.Popen(['Xvfb', ':99', '-screen', '0', '2048x1536x24', '-nolisten', 'tcp',
                                 '-auth', str(authority)], stdout=xlog, stderr=xlog)
        client = None
        try:
            for _ in range(40):
                if xvfb.poll() is not None:
                    raise RuntimeError('Xvfb failed to start')
                if Path('/tmp/.X11-unix/X99').exists():
                    break
                time.sleep(.1)
            client = subprocess.Popen(['xfreerdp', f'/v:127.0.0.1:{port}', '/u:greeter',
                                       '/from-stdin:force', f'/size:{requested}', '/gfx:AVC420',
                                       f'/cert:fingerprint:sha256:{fingerprint}', '/log-level:WARN', '-clipboard'],
                                      env=env, stdin=subprocess.PIPE, stdout=clog, stderr=clog, text=True)
            client.stdin.write(password + '\n')
            client.stdin.close()
            actual = initial
            stable = 0
            deadline = time.monotonic() + 25
            while time.monotonic() < deadline and client.poll() is None:
                actual = geometry()
                awake = dpms() == 'on' if check_dpms else True
                stable = stable + 1 if actual == (width & ~7, height & ~1) and awake else 0
                if stable >= 5:
                    break
                time.sleep(.5)
            result = {'account': account, 'requested': requested, 'before_geometry': initial,
                      'actual_geometry': actual, 'matched_stably': stable >= 5,
                      'client_running': client.poll() is None,
                      'before_dpms': initial_dpms, 'after_dpms': dpms() if check_dpms else None,
                      'before_pids': before, 'after_pids': {name: pid(name) for name in before}}
            result['pids_unchanged'] = result['before_pids'] == result['after_pids']
            print(json.dumps(result), flush=True)
            if not result['matched_stably'] or not result['pids_unchanged'] or not result['client_running']:
                clog.flush()
                print((directory / 'client.log').read_text().replace(password, '[REDACTED]')[-4000:], flush=True)
                raise SystemExit(1)
        finally:
            for process in (client, xvfb):
                if process is not None and process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=8)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
