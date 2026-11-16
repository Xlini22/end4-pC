"""Run: python3 tests/native-glass-loader-check.py (no compositor changes)."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile

spec = importlib.util.spec_from_file_location('backend', Path(__file__).resolve().parents[1] / 'scripts/glass/native/backend.py')
backend = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backend)
with tempfile.TemporaryDirectory() as temporary:
    os.environ['XDG_DATA_HOME'] = temporary
    directory = Path(temporary) / 'end4-pC/native-glass'
    directory.mkdir(parents=True)
    binary = directory / 'hyprglass.so'
    binary.write_bytes(b'test binary')
    metadata = {'abiHash': 'matching-abi', 'sha256': hashlib.sha256(binary.read_bytes()).hexdigest()}
    manifest = directory / 'manifest.json'
    calls = []
    loaded = []
    lua = True

    def query(*args):
        calls.append(args)
        if args == ('plugin', 'list', '-j'):
            return json.dumps(loaded)
        if args == ('version', '-j'):
            return json.dumps({'abiHash': 'matching-abi'})
        if args == ('eval', 'return true'):
            return 'ok' if lua else 'eval requires the Lua parser'
        assert args == ('plugin', 'load', str(binary)), args
        loaded.append({'name': 'hyprglass', 'version': backend.VERSION})
        return 'ok'
    backend.query = query
    assert not backend.status(True)['available']  # missing manifest
    for invalid in ({**metadata, 'abiHash': 'old-abi'}, {**metadata, 'sha256': 'incorrect'}):
        manifest.write_text(json.dumps(invalid))
        assert not backend.status(True)['available']
    assert not any(call[:2] == ('plugin', 'load') for call in calls), calls
    manifest.write_text(json.dumps(metadata))
    assert not backend.status()['available']  # probing alone must never load
    os.environ['HYPRLAND_INSTANCE_SIGNATURE'] = 'current-session'
    manifest.write_text(json.dumps({**metadata, 'deferInstance': 'current-session'}))
    assert not backend.status(True)['available'], 'A Quickshell reload must not load the plugin in the deferred session'
    os.environ.pop('HYPRLAND_INSTANCE_SIGNATURE')
    assert not backend.status(True)['available'], 'Without a session identity, deferred loading must stay blocked'
    assert not any(call[:2] == ('plugin', 'load') for call in calls), calls
    os.environ['HYPRLAND_INSTANCE_SIGNATURE'] = 'next-session'
    assert backend.status(True)['available']
    assert sum(call[:2] == ('plugin', 'load') for call in calls) == 1
    assert backend.status()['lua'] and backend.status()['enhanced'] and backend.status()['frosted'] and backend.status()['contrast']
    assert backend.status()['profiles'] and backend.status()['topBarOptics']
    assert backend.status()['barVisibility'] and backend.status()['darkening'] and backend.status()['uniformDarkening']
    loaded[0]['version'] = 'end4-live-0.6.4-r34'
    assert backend.status()['available'] and backend.status()['uniformDarkening'] and backend.status()['windowFrosted']
    loaded[0]['version'] = 'end4-live-0.6.4-r31'
    assert backend.status()['uniformDarkening']
    loaded[0]['version'] = 'end4-live-0.6.4-r30'
    assert backend.status()['uniformDarkening']
    loaded[0]['version'] = 'end4-live-0.6.4-r29'
    assert backend.status()['uniformDarkening']
    loaded[0]['version'] = 'end4-live-0.6.4-r28'
    assert not backend.status()['uniformDarkening']
    assert backend.status()['barVisibility'] and backend.status()['darkening']
    loaded[0]['version'] = 'end4-live-0.6.4-r27'
    assert backend.status()['barVisibility'] and backend.status()['darkening']
    loaded[0]['version'] = 'end4-live-0.6.4-r26'
    assert backend.status()['barVisibility'] and not backend.status()['darkening']
    loaded[0]['version'] = backend.VERSION
    assert backend.status()['windowFrosted'], 'Current Dashboard build is enabled for authorized testing with the IPC fix'
    lua = False
    assert backend.status()['available'] and not backend.status()['lua']
    loaded[0]['version'] = 'end4-live-0.6.4-r25'
    calls.clear()
    assert not backend.status(True)['barVisibility']
    assert all(backend.status()[key] for key in ('available', 'profiles', 'topBarOptics', 'windowFrosted', 'frosted', 'contrast', 'enhanced'))
    assert not any(call[:2] in (('plugin', 'load'), ('plugin', 'unload')) for call in calls), calls
    loaded[0]['version'] = 'end4-live-0.6.4-r24'
    calls.clear()
    assert all(backend.status(True)[key] for key in ('available', 'profiles', 'topBarOptics', 'windowFrosted', 'frosted', 'contrast', 'enhanced'))
    assert not any(call[:2] in (('plugin', 'load'), ('plugin', 'unload')) for call in calls), calls
    loaded[0]['version'] = 'end4-live-0.6.4-r23'
    calls.clear()
    assert all(backend.status(True)[key] for key in ('available', 'profiles', 'topBarOptics', 'windowFrosted', 'frosted', 'contrast', 'enhanced'))
    assert not any(call[:2] in (('plugin', 'load'), ('plugin', 'unload')) for call in calls), calls
    loaded[0]['version'] = 'end4-live-0.6.4-r22'
    assert all(backend.status()[key] for key in ('available', 'profiles', 'topBarOptics', 'windowFrosted', 'frosted', 'contrast', 'enhanced'))
    loaded[0]['version'] = 'end4-live-0.6.4-r21'
    assert all(backend.status()[key] for key in ('available', 'profiles', 'topBarOptics', 'windowFrosted', 'frosted', 'contrast', 'enhanced'))
    loaded[0]['version'] = 'end4-live-0.6.4-r20'
    assert backend.status()['topBarOptics'] and not backend.status()['profiles'] and not backend.status()['windowFrosted']
    loaded[0]['version'] = 'end4-live-0.6.4-r19'
    assert backend.status()['available'] and backend.status()['topBarOptics']
    assert backend.status()['contrast'] and backend.status()['frosted'] and backend.status()['enhanced']
    assert not backend.status()['windowFrosted']
    loaded[0]['version'] = 'end4-live-0.6.4-r18'
    assert backend.status()['contrast'] and not backend.status()['topBarOptics'] and not backend.status()['windowFrosted']
    loaded[0]['version'] = 'end4-live-0.6.4-r17'
    assert backend.status()['contrast'] and not backend.status()['windowFrosted']
    loaded[0]['version'] = 'end4-live-0.6.4-r16'
    assert backend.status()['frosted'] and backend.status()['enhanced'] and not backend.status()['contrast']
    loaded[0]['version'] = 'end4-live-0.6.4-r15'
    assert backend.status()['frosted'] and backend.status()['enhanced']
    loaded[0]['version'] = 'end4-live-0.6.4-r14'
    assert backend.status()['frosted'] and backend.status()['enhanced']
    loaded[0]['version'] = 'end4-live-0.6.4-r13'
    assert backend.status()['frosted'] and backend.status()['enhanced']
    loaded[0]['version'] = 'end4-live-0.6.4-r12'
    assert backend.status()['frosted'] and backend.status()['enhanced']
    loaded[0]['version'] = 'end4-live-0.6.4-r10'
    assert backend.status()['frosted']
    loaded[0]['version'] = 'end4-live-0.6.4-r11'
    assert backend.status()['available'] and backend.status()['enhanced'] and not backend.status()['frosted']
    for version in ('end4-live-0.6.4-r9', 'end4-live-0.6.4-r8', 'end4-live-0.6.4-r7', 'end4-live-0.6.4-r6', 'end4-live-0.6.4-r5', 'end4-live-0.6.4-r4'):
        loaded[0]['version'] = version
        assert backend.status()['available'] and backend.status()['enhanced']
        assert not backend.status()['frosted']
    loaded[0]['version'] = 'end4-live-0.6.4-r3'
    assert backend.status()['available'] and not backend.status()['enhanced']
    loaded[0]['version'] = 'end4-live-0.6.4-r2'
    assert backend.status()['available']  # Do not disrupt the session awaiting an upgrade.
    loaded[0]['version'] = 'foreign-version'
    calls.clear()
    assert not backend.status(True)['available']
    assert calls == [('plugin', 'list', '-j')], calls
print('Native loader validates ABI/hash, defers current/unknown sessions and loads verified builds in new sessions')
