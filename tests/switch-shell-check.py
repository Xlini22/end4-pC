#!/usr/bin/env python3
"""CPU-only selection, plugin parking, and rejection checks."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile

spec = importlib.util.spec_from_file_location('switch_shell', Path(__file__).parents[1] / 'scripts/switch-shell.py')
switch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(switch)
with tempfile.TemporaryDirectory() as directory:
    home = Path(directory)
    for shell in ['ii', 'end4-pC']:
        p = home / f'.config/quickshell/{shell}/shell.qml'
        p.parent.mkdir(parents=True)
        p.touch()
    config = home / '.config/hypr/custom/variables.lua'
    config.parent.mkdir(parents=True)
    config.write_text('hl.env("qsConfig", "ii")\n')
    settings = home / '.config/illogical-impulse/config.json'
    settings.parent.mkdir(parents=True)
    settings.write_text(json.dumps({'unrelated': {'keep': 17}}))
    native = home / '.local/share/end4-pC/native-glass'
    native.mkdir(parents=True)
    (home / '.local/state/end4-pC/shell-switches').mkdir(parents=True)
    source = native / 'hyprglass.so.disabled-for-ii-test'
    source.write_bytes(b'test binary, never loaded')
    manifest = native / 'manifest.json'
    manifest.write_text(json.dumps({'sha256': hashlib.sha256(source.read_bytes()).hexdigest()}))
    switch.select(home, 'end4-pC', 'session-one')
    assert 'end4-pC' in config.read_text()
    assert json.loads(manifest.read_text())['deferInstance'] == 'session-one'
    assert (native / 'hyprglass.so').read_bytes() == source.read_bytes()
    glass = json.loads(settings.read_text())['background']['widgets']['glass']
    assert glass['enable'] and glass['nativePlugin'] and glass['source'] == 'windows'
    assert json.loads(settings.read_text())['unrelated'] == {'keep': 17}
    switch.select(home, 'ii', 'session-one')
    assert config.read_text() == 'hl.env("qsConfig", "ii")\n'
    assert not (native / 'hyprglass.so').exists()
    assert not json.loads(settings.read_text())['background']['widgets']['glass']['nativePlugin']
    # The settings control must enable the plugin without selecting a different shell.
    switch.select(home, None, 'session-one', True)
    assert config.read_text() == 'hl.env("qsConfig", "ii")\n'
    switch.select(home, None, 'session-one', False)
    switch.select(home, 'end4-pC', 'session-two')
    assert json.loads(manifest.read_text())['deferInstance'] == 'session-two'
    switch.select(home, 'ii', 'session-two')
    manifest.write_text(json.dumps({'sha256': 'invalid'}))
    before = config.read_bytes()
    try:
        switch.select(home, 'end4-pC', 'session-three')
        raise AssertionError('Corrupt binary accepted')
    except ValueError:
        pass
    assert config.read_bytes() == before
    assert not (native / 'hyprglass.so').exists()
    # A missing session signature must not change preferences or install the binary.
    snapshot = settings.read_bytes()
    try:
        switch.select(home, None, '', True)
        raise AssertionError('Missing session accepted')
    except ValueError:
        pass
    assert settings.read_bytes() == snapshot
    # The running session is excluded before publishing the windows/native preference.
    manifest.write_text(json.dumps({'sha256': hashlib.sha256(source.read_bytes()).hexdigest()}))
    original_write = switch.write
    def checked_write(path, data):
        if path == settings:
            assert json.loads(manifest.read_text())['deferInstance'] == 'ordering-test'
        original_write(path, data)
    switch.write = checked_write
    switch.select(home, None, 'ordering-test', True)
    switch.write = original_write
print('switch-shell: OK')
