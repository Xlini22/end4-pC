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
revision = '3f936be7faa7f49180ab5167fa82066ef6d79891'
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
        'notify-send': "#!/bin/sh\nprintf 'default\\n'\n",
        'uwsm-app': '#!/usr/bin/python3\nimport json,os,sys\nwith open(os.environ["CALLS"],"a") as f: f.write(json.dumps(sys.argv[1:])+"\\n")\n',
    }.items():
        target = helpers / command
        target.write_text(body)
        target.chmod(0o755)
    calls = folder / 'calls'
    env = {**os.environ, 'PATH': f'{helpers}:/usr/bin', 'CALLS': str(calls),
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
