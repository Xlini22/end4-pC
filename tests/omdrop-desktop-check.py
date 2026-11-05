"""Check the desktop patch against a pinned, external Omdrop Git checkout.

Run: python3 tests/omdrop-desktop-check.py /path/to/omdrop-plugin
Only temporary files are modified; no receiver or radio is started.
"""
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

repo = Path(__file__).resolve().parents[1]
revision = 'c73e8a696bee6ade33c3aad920bba9240de2481a'
if len(sys.argv) != 2:
    raise SystemExit(__doc__)
checkout = Path(sys.argv[1]).resolve()
archive = subprocess.check_output(['git', '-C', str(checkout), 'archive', revision])
with tempfile.TemporaryDirectory(prefix='omdrop desktop ') as directory:
    folder = Path(directory)
    backend = folder / 'backend with spaces'
    backend.mkdir()
    with tarfile.open(fileobj=io.BytesIO(archive)) as source:
        source.extractall(backend, filter='data')
    subprocess.run(['patch', '--batch', '--forward', '-p1', '-i',
                    str(repo / 'scripts/airdrop/omdrop-desktop.patch')],
                   cwd=backend, check=True, capture_output=True)
    cli = backend / 'bin/omdrop'
    subprocess.run(['bash', '-n', str(cli)], check=True)
    template = (backend / 'share/airdrop-receiver.service').read_text()
    unit = folder / 'airdrop-receiver.service'
    unit.write_text(template.replace('@PLUGIN_DIR@', str(backend)))
    result = subprocess.run(['systemd-analyze', '--user', 'verify', '--man=no', str(unit)],
                            capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stdout + result.stderr
    print('Receiver service validation with spaces passed')

    helpers = folder / 'helpers'
    helpers.mkdir()
    for command, body in {
        'notify-send': '#!/usr/bin/python3\nimport json,os,sys\nwith open(os.environ["NOTIFICATIONS"],"a") as f: f.write(json.dumps(sys.argv[1:])+"\\n")\nprint("default")\n',
        'uwsm-app': '#!/usr/bin/python3\nimport json,os,sys\nwith open(os.environ["CALLS"],"a") as f: f.write(json.dumps(sys.argv[1:])+"\\n")\n',
        'xdg-mime': '#!/bin/sh\ncase "$2" in filetype) echo image/png ;; default) [ -n "$OMDROP_TEST_NO_DEFAULT" ] || echo image-viewer.desktop ;; esac\n',
        'nautilus': '#!/bin/sh\nexit 0\n',
        'heif-convert': '#!/usr/bin/python3\nfrom pathlib import Path\nimport sys\nPath(sys.argv[-1]).write_bytes(b"JPEG preview")\n',
        'magick': '#!/bin/sh\nexit 1\n',
    }.items():
        target = helpers / command
        target.write_text(body)
        target.chmod(0o755)
    calls = folder / 'calls'
    notifications = folder / 'notifications'
    env = {**os.environ, 'PATH': f'{helpers}:/usr/bin', 'CALLS': str(calls),
           'NOTIFICATIONS': str(notifications), 'OMDROP_IMPLEMENTATION': 'python',
           'OMDROP_TEST_NO_DEFAULT': '',
           'XDG_CONFIG_HOME': str(folder / 'config'),
           'XDG_RUNTIME_DIR': str(folder / 'runtime')}
    received = folder / 'photo with spaces $(false).png'
    received.write_bytes(b'PNG')
    subprocess.run([str(cli), 'act', 'notify-native', str(received)],
                   env=env, capture_output=True, check=True, timeout=10)
    assert json.loads(calls.read_text().splitlines()[-1]) == ['--', 'xdg-open', str(received)]
    url = 'https://example.org/?q=$(false)&x=a%20b'
    shortcut = folder / 'page.url'
    shortcut.write_text('[InternetShortcut]\nURL=' + url + '\n')
    subprocess.run([str(cli), 'open-link', str(shortcut)],
                   env=env, capture_output=True, check=True, timeout=10)
    assert json.loads(calls.read_text().splitlines()[-1]) == ['--', 'xdg-open', url]
    subprocess.run([str(cli), 'act', 'shell', str(received)],
                   env=env, capture_output=True, check=True, timeout=10)
    assert json.loads(calls.read_text().splitlines()[-1]) == ['--', 'kitty']
    print('Native notification, browser and terminal argument checks passed')
    subprocess.run([str(cli), 'act', 'notify-native', str(received)],
                   env={**env, 'OMDROP_TEST_NO_DEFAULT': '1'}, capture_output=True, check=True, timeout=10)
    assert json.loads(calls.read_text().splitlines()[-1]) == ['--', 'nautilus', '--select', str(received)]
    subprocess.run([str(cli), 'handle', str(received)],
                   env=env, capture_output=True, check=True, timeout=10)
    assert json.loads(calls.read_text().splitlines()[-1]) == ['--', str(cli), 'act', 'notify-native', str(received), '--image', str(received)]
    heic = folder / 'photo with spaces $(false).heic'
    heic.write_bytes(b'HEIC input')
    subprocess.run([str(cli), 'handle', str(heic)], env=env,
                   capture_output=True, check=True, timeout=10)
    command = json.loads(calls.read_text().splitlines()[-1])
    assert command[:6] == ['--', str(cli), 'act', 'notify-native', str(heic), '--image'], command
    preview = Path(command[6])
    assert preview.is_file() and preview.suffix == '.jpg'
    subprocess.run(command[1:], env=env, capture_output=True, check=True, timeout=10)
    options = json.loads(notifications.read_text().splitlines()[-1])
    assert options[options.index('--icon') + 1] == str(preview)
    invalid = subprocess.run([str(cli), 'act', 'notify-native', str(heic), '--unexpected'],
                             env=env, capture_output=True, timeout=10)
    assert invalid.returncode == 2
    print('Native file-manager fallback, bounded preview forwarding and option validation passed')
