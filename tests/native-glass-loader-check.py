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
    assert backend.status(True)['available']
    assert sum(call[:2] == ('plugin', 'load') for call in calls) == 1
    assert backend.status()['lua'] and backend.status()['enhanced'] and backend.status()['frosted']
    lua = False
    assert backend.status()['available'] and not backend.status()['lua']
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
print('Native loader rejects ABI/hash mismatches and foreign builds; loads only the verified build')
