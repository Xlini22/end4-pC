"""Run: python3 tests/native-glass-loader-check.py (no compositor changes)."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
from unittest.mock import patch
import subprocess

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
    for version, temporal in [(backend.CANDIDATE_VERSION, False), (backend.PREVIOUS_TEMPORAL_VERSION, True), (backend.TEMPORAL_VERSION, True), (backend.VISIBILITY_VERSION, True), (backend.SCENE_VERSION, True), (backend.REFLECTIONS_VERSION, True), (backend.INITIAL_DARKENING_VERSION, True), (backend.SIDEBAR_DARKENING_VERSION, True), (backend.COHERENCE_VERSION, True), (backend.SECTION_VERSION, True), (backend.FADE_VERSION, True)]:
        loaded[0]['version'] = version
        status = backend.status()
        assert status['available'] and status['uniformDarkening'] and status['windowFrosted']
        assert status['sectionDarkening'] is (version in (backend.SECTION_VERSION, backend.FADE_VERSION))
        assert status['fadeContinuity'] is (version == backend.FADE_VERSION)
        assert status['temporalDarkening'] is temporal
        assert status['darkeningStrength'] is (version in (backend.COHERENCE_VERSION, backend.SECTION_VERSION, backend.FADE_VERSION))
        assert status['darkeningVisibility'] is (version in (backend.VISIBILITY_VERSION, backend.SCENE_VERSION, backend.REFLECTIONS_VERSION, backend.INITIAL_DARKENING_VERSION, backend.SIDEBAR_DARKENING_VERSION, backend.COHERENCE_VERSION, backend.SECTION_VERSION, backend.FADE_VERSION))
    for version in (backend.OVERVIEW_VERSION, backend.OVERVIEW_FROST_VERSION):
        loaded[0]['version'] = version
        current = backend.status()
        assert all(current[key] for key in ('available', 'overviewProfiles', 'profiles', 'frosted', 'sectionDarkening', 'fadeContinuity', 'darkeningStrength'))
        assert not any(call[:2] == ('plugin', 'unload') for call in calls)
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

# Every byte, boot identity and compositor response below is fake.
with tempfile.TemporaryDirectory() as temporary, patch.dict(os.environ, {
    'XDG_DATA_HOME': temporary, 'HYPRLAND_INSTANCE_SIGNATURE': 'preparation-session',
}), patch.object(backend, 'boot_id', return_value='11111111-1111-1111-1111-111111111111') as current_boot:
    directory = backend.install_directory()
    directory.mkdir(parents=True)
    staging = Path(temporary) / 'staging'
    staging.mkdir()
    binary = staging / 'hyprglass.so'
    binary.write_bytes(b'fake staged plugin; never executable')
    metadata = {'abiHash': 'matching-abi', 'sha256': hashlib.sha256(binary.read_bytes()).hexdigest()}
    (staging / 'manifest.json').write_text(json.dumps(metadata))
    ticket = directory / 'test-once.json'
    calls, events, loaded = [], [], []
    failure = None
    real_sync = backend.sync_directory

    def sync(path):
        real_sync(path)
        events.append('persisted')

    def once_query(*args):
        calls.append(args)
        if args == ('plugin', 'list', '-j'):
            return json.dumps(loaded)
        if args == ('version', '-j'):
            return json.dumps({'abiHash': 'matching-abi'})
        if args == ('eval', 'return true'):
            return 'ok'
        assert args == ('plugin', 'load', str(binary)), args
        assert not ticket.exists(), 'Consume before entering native code'
        assert list(directory.glob('test-used-*.json')), 'Keep the consumed record'
        assert events[-1] == 'persisted', 'Persist consumption before native code'
        events.append('load')
        # A second detector cannot enter while the first is loading.
        try:
            backend.status(True)
        except BlockingIOError:
            pass
        else:
            raise AssertionError('Concurrent ensure was not blocked')
        if isinstance(failure, Exception):
            raise failure
        if failure:
            return failure
        loaded.append({'name': 'hyprglass', 'version': backend.CANDIDATE_VERSION})
        return 'ok'

    def expect_error(kind, action):
        try:
            action()
        except kind:
            return
        raise AssertionError(f'Expected {kind.__name__}')

    def prepare():
        os.environ['HYPRLAND_INSTANCE_SIGNATURE'] = 'preparation-session'
        backend.arm_once(staging)
        os.environ['HYPRLAND_INSTANCE_SIGNATURE'] = 'test-session'

    with patch.object(backend, 'query', side_effect=once_query), patch.object(backend, 'sync_directory', side_effect=sync):
        os.environ.pop('HYPRLAND_INSTANCE_SIGNATURE')
        expect_error(ValueError, lambda: backend.arm_once(staging))
        os.environ['HYPRLAND_INSTANCE_SIGNATURE'] = 'preparation-session'
        ordinary = directory / 'hyprglass.so'
        ordinary.symlink_to(directory / 'missing-plugin')
        expect_error(ValueError, lambda: backend.arm_once(staging))
        ordinary.unlink()
        loaded.append({'name': 'hyprglass', 'version': 'foreign'})
        expect_error(ValueError, lambda: backend.arm_once(staging))
        loaded.clear()
        for invalid in ({**metadata, 'abiHash': 'wrong'}, {**metadata, 'sha256': 'wrong'}, []):
            (staging / 'manifest.json').write_text(json.dumps(invalid))
            expect_error(ValueError, lambda: backend.arm_once(staging))
            assert not ticket.exists()
        (staging / 'manifest.json').write_text(json.dumps(metadata))

        backend.arm_once(staging)
        pending = ticket.read_bytes()
        expect_error(FileExistsError, lambda: backend.arm_once(staging))
        assert ticket.read_bytes() == pending
        assert not backend.status()['available'] and ticket.read_bytes() == pending
        assert not backend.status(True)['available'], 'Never load in the preparation session'
        os.environ.pop('HYPRLAND_INSTANCE_SIGNATURE')
        assert not backend.status(True)['available'], 'An unknown session must not consume the test'
        os.environ['HYPRLAND_INSTANCE_SIGNATURE'] = 'test-session'
        assert backend.status(True)['available']
        assert backend.status(True)['available']
        assert events.count('load') == 1
        loaded.clear()  # A new process/session must not retry the consumed test.
        assert not backend.status(True)['available']
        assert events.count('load') == 1

        prepare()
        current_boot.return_value = '22222222-2222-2222-2222-222222222222'
        assert 'expired' in backend.status(True)['reason']
        assert ticket.exists() and events.count('load') == 1
        calls.clear()
        backend.cancel_once()
        backend.cancel_once()
        assert not calls and not ticket.exists(), 'Cancellation must not query or unload the compositor'
        current_boot.return_value = '11111111-1111-1111-1111-111111111111'

        for failure in ['mock load error', subprocess.TimeoutExpired('mock-hyprctl', 10)]:
            prepare()
            count = events.count('load')
            if isinstance(failure, Exception):
                expect_error(type(failure), lambda: backend.status(True))
            else:
                assert not backend.status(True)['available']
            assert not ticket.exists() and events.count('load') == count + 1
            assert not backend.status(True)['available']
            assert events.count('load') == count + 1, 'Failed loads must never retry'
        failure = None

        prepare()
        with patch.object(backend, 'sync_directory', side_effect=OSError('mock fsync failure')):
            expect_error(OSError, lambda: backend.status(True))
        assert not ticket.exists(), 'A persistence error must block loading and consume the attempt'
        assert not backend.status(True)['available']

        with patch.object(backend, 'sync_directory', side_effect=OSError('mock fsync failure')):
            expect_error(OSError, lambda: backend.arm_once(staging))
        assert not ticket.exists(), 'Failed arming must not leave a valid ticket'

        prepare()
        payload = json.loads(ticket.read_text())
        payload['sha256'] = 'changed'
        ticket.write_text(json.dumps(payload))
        assert not backend.status(True)['available'] and ticket.exists()
        payload['sha256'] = metadata['sha256']
        payload['testId'] = 'invalid UUID'
        ticket.write_text(json.dumps(payload))
        expect_error(ValueError, lambda: backend.status(True))
        backend.cancel_once()

        prepare()
        payload = json.loads(ticket.read_text())
        used = directory / ('test-used-' + payload['testId'] + '.json')
        used.write_text('{}')
        assert not backend.status(True)['available'], 'A recorded attempt cannot be repeated'
        backend.cancel_once()

        with backend.installation_lock():
            for action in [lambda: backend.arm_once(staging), lambda: backend.status(True), backend.cancel_once]:
                expect_error(BlockingIOError, action)
        assert not any(call[:2] == ('plugin', 'unload') for call in calls)
        assert not ordinary.exists() and not ticket.exists()
print('One-session loader: boot expiry, durable consumption, cancellation, failures and concurrent requests passed (mock only)')
