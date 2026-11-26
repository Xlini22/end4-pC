"""Probe/load only the ABI-matched end4 HyprGlass build installed by the user."""
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import uuid

VERSION = 'end4-live-0.6.4-r35'
CANDIDATE_VERSION = 'end4-live-0.6.4-r36-candidate'
TEMPORAL_VERSION = 'end4-live-0.6.4-r38-candidate'
VISIBILITY_VERSION = 'end4-live-0.6.4-r39-candidate'
SCENE_VERSION = 'end4-live-0.6.4-r40-candidate'
REFLECTIONS_VERSION = 'end4-live-0.6.4-r41-candidate'
FADE_VERSION = 'end4-live-0.6.4-r46-candidate'
OVERVIEW_VERSION = 'end4-live-0.6.4-r47-overview'
OVERVIEW_FROST_VERSION = 'end4-live-0.6.4-r49-overview-frost'
SECTION_VERSION = 'end4-live-0.6.4-r45-candidate'
COHERENCE_VERSION = 'end4-live-0.6.4-r44-candidate'
SIDEBAR_DARKENING_VERSION = 'end4-live-0.6.4-r43-candidate'
INITIAL_DARKENING_VERSION = 'end4-live-0.6.4-r42-candidate'
PREVIOUS_TEMPORAL_VERSION = 'end4-live-0.6.4-r37-candidate'


def install_directory():
    return Path(os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local/share'))) / 'end4-pC/native-glass'


def boot_id():
    return str(uuid.UUID(Path('/proc/sys/kernel/random/boot_id').read_text().strip()))


def sync_directory(directory):
    descriptor = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


@contextmanager
def installation_lock():
    directory = install_directory()
    directory.mkdir(parents=True, exist_ok=True)
    # ponytail: one local flock serializes arm/cancel/load; never wait on another detector.
    with (directory / 'loader.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield directory


def arm_once(staging):
    with installation_lock():
        return _arm_once(staging)


def _arm_once(staging):
    directory = install_directory()
    instance = os.environ.get('HYPRLAND_INSTANCE_SIGNATURE')
    if not instance:
        raise ValueError('Cannot arm a test without the current Hyprland session identity')
    if os.path.lexists(directory / 'hyprglass.so'):
        raise ValueError('Remove the ordinary plugin installation before arming a one-session test')
    if any(plugin.get('name') == 'hyprglass' for plugin in json.loads(query('plugin', 'list', '-j'))):
        raise ValueError('HyprGlass is already loaded; no hot replacement is permitted')
    staging = Path(staging).resolve(strict=True)
    binary = (staging / 'hyprglass.so').resolve(strict=True)
    metadata = json.loads((staging / 'manifest.json').read_text())
    if not isinstance(metadata, dict) or not metadata.get('abiHash'):
        raise ValueError('Invalid staging manifest')
    if metadata['abiHash'] != json.loads(query('version', '-j')).get('abiHash'):
        raise ValueError('Staged ABI does not match Hyprland')
    if metadata.get('sha256') != hashlib.sha256(binary.read_bytes()).hexdigest():
        raise ValueError('Staged binary does not match its manifest')
    metadata.update(binary=str(binary), testBoot=boot_id(), deferInstance=instance, testId=uuid.uuid4().hex)
    directory.mkdir(parents=True, exist_ok=True)
    # Exclusive publication: never replace an already armed test or expose partial JSON.
    with tempfile.NamedTemporaryFile(mode='w', dir=directory) as temporary:
        json.dump(metadata, temporary)
        temporary.flush()
        os.fsync(temporary.fileno())
        os.link(temporary.name, directory / 'test-once.json')
    try:
        sync_directory(directory)
    except OSError:
        (directory / 'test-once.json').unlink()
        raise
    return {'available': False, 'reason': 'One-session test armed for the next login in this boot; reboot cancels it'}


def cancel_once():
    with installation_lock() as directory:
        (directory / 'test-once.json').unlink(missing_ok=True)
        sync_directory(directory)
    return {'available': False, 'reason': 'Pending test cancelled; an already loaded plugin is not unloaded'}


def query(*args):
    result = subprocess.run(['hyprctl', *args], capture_output=True, text=True, timeout=10, check=True)
    return result.stdout.strip()


def status(ensure=False):
    if not ensure:
        return _status(False)
    with installation_lock():
        return _status(True)


def _status(ensure):
    plugins = json.loads(query('plugin', 'list', '-j'))
    plugin = next((p for p in plugins if p.get('name') == 'hyprglass'), None)
    if plugin:
        overview_profiles = plugin.get("version") in (OVERVIEW_VERSION, OVERVIEW_FROST_VERSION)
        if overview_profiles:
            plugin = {**plugin, "version": FADE_VERSION}
        # The previous build may remain mapped until the current session exits.
        if plugin.get('version') not in (VERSION, CANDIDATE_VERSION, TEMPORAL_VERSION, PREVIOUS_TEMPORAL_VERSION, VISIBILITY_VERSION, SCENE_VERSION, REFLECTIONS_VERSION, INITIAL_DARKENING_VERSION, SIDEBAR_DARKENING_VERSION, COHERENCE_VERSION, SECTION_VERSION, 'end4-live-0.6.4-r34', 'end4-live-0.6.4-r33', 'end4-live-0.6.4-r32', 'end4-live-0.6.4-r31', 'end4-live-0.6.4-r30', 'end4-live-0.6.4-r29', 'end4-live-0.6.4-r28', 'end4-live-0.6.4-r27', 'end4-live-0.6.4-r26', 'end4-live-0.6.4-r25', 'end4-live-0.6.4-r24', 'end4-live-0.6.4-r23', 'end4-live-0.6.4-r22', 'end4-live-0.6.4-r21', 'end4-live-0.6.4-r20', 'end4-live-0.6.4-r19', 'end4-live-0.6.4-r18', 'end4-live-0.6.4-r17', 'end4-live-0.6.4-r16', 'end4-live-0.6.4-r15', 'end4-live-0.6.4-r14', 'end4-live-0.6.4-r13', 'end4-live-0.6.4-r12', 'end4-live-0.6.4-r11', 'end4-live-0.6.4-r10', 'end4-live-0.6.4-r9', 'end4-live-0.6.4-r8', 'end4-live-0.6.4-r7', 'end4-live-0.6.4-r6', 'end4-live-0.6.4-r5', 'end4-live-0.6.4-r4', 'end4-live-0.6.4-r3', 'end4-live-0.6.4-r2', FADE_VERSION):
            return {'available': False, 'reason': 'A different HyprGlass build is loaded'}
        # Keep existing capabilities while r34 awaits the next login; negotiate darkening separately.
        return {'available': True, 'overviewProfiles': overview_profiles, 'sectionDarkening': plugin.get('version') in (SECTION_VERSION, FADE_VERSION), 'fadeContinuity': plugin.get('version') == FADE_VERSION, 'darkeningStrength': plugin.get('version') in (COHERENCE_VERSION, SECTION_VERSION, FADE_VERSION), 'darkeningVisibility': plugin.get('version') in (VISIBILITY_VERSION, SCENE_VERSION, REFLECTIONS_VERSION, INITIAL_DARKENING_VERSION, SIDEBAR_DARKENING_VERSION, COHERENCE_VERSION, SECTION_VERSION, FADE_VERSION), 'temporalDarkening': plugin.get('version') in (TEMPORAL_VERSION, PREVIOUS_TEMPORAL_VERSION, VISIBILITY_VERSION, SCENE_VERSION, REFLECTIONS_VERSION, INITIAL_DARKENING_VERSION, SIDEBAR_DARKENING_VERSION, COHERENCE_VERSION, SECTION_VERSION, FADE_VERSION), 'uniformDarkening': plugin.get('version') in (VERSION, CANDIDATE_VERSION, TEMPORAL_VERSION, PREVIOUS_TEMPORAL_VERSION, VISIBILITY_VERSION, SCENE_VERSION, REFLECTIONS_VERSION, INITIAL_DARKENING_VERSION, SIDEBAR_DARKENING_VERSION, COHERENCE_VERSION, SECTION_VERSION, 'end4-live-0.6.4-r34', 'end4-live-0.6.4-r33', 'end4-live-0.6.4-r32', 'end4-live-0.6.4-r31', 'end4-live-0.6.4-r30', 'end4-live-0.6.4-r29', FADE_VERSION), 'darkening': plugin.get('version') in (VERSION, CANDIDATE_VERSION, TEMPORAL_VERSION, PREVIOUS_TEMPORAL_VERSION, VISIBILITY_VERSION, SCENE_VERSION, REFLECTIONS_VERSION, INITIAL_DARKENING_VERSION, SIDEBAR_DARKENING_VERSION, COHERENCE_VERSION, SECTION_VERSION, 'end4-live-0.6.4-r34', 'end4-live-0.6.4-r33', 'end4-live-0.6.4-r32', 'end4-live-0.6.4-r31', 'end4-live-0.6.4-r30', 'end4-live-0.6.4-r29', 'end4-live-0.6.4-r28', 'end4-live-0.6.4-r27', FADE_VERSION), 'barVisibility': plugin.get('version') in (VERSION, CANDIDATE_VERSION, TEMPORAL_VERSION, PREVIOUS_TEMPORAL_VERSION, VISIBILITY_VERSION, SCENE_VERSION, REFLECTIONS_VERSION, INITIAL_DARKENING_VERSION, SIDEBAR_DARKENING_VERSION, COHERENCE_VERSION, SECTION_VERSION, 'end4-live-0.6.4-r34', 'end4-live-0.6.4-r33', 'end4-live-0.6.4-r32', 'end4-live-0.6.4-r31', 'end4-live-0.6.4-r30', 'end4-live-0.6.4-r29', 'end4-live-0.6.4-r28', 'end4-live-0.6.4-r27', 'end4-live-0.6.4-r26', FADE_VERSION), 'profiles': plugin.get('version') in (VERSION, CANDIDATE_VERSION, TEMPORAL_VERSION, PREVIOUS_TEMPORAL_VERSION, VISIBILITY_VERSION, SCENE_VERSION, REFLECTIONS_VERSION, INITIAL_DARKENING_VERSION, SIDEBAR_DARKENING_VERSION, COHERENCE_VERSION, SECTION_VERSION, 'end4-live-0.6.4-r34', 'end4-live-0.6.4-r33', 'end4-live-0.6.4-r32', 'end4-live-0.6.4-r31', 'end4-live-0.6.4-r30', 'end4-live-0.6.4-r29', 'end4-live-0.6.4-r28', 'end4-live-0.6.4-r27', 'end4-live-0.6.4-r26', 'end4-live-0.6.4-r25', 'end4-live-0.6.4-r24', 'end4-live-0.6.4-r23', 'end4-live-0.6.4-r22', 'end4-live-0.6.4-r21', FADE_VERSION), 'topBarOptics': plugin.get('version') in (VERSION, CANDIDATE_VERSION, TEMPORAL_VERSION, PREVIOUS_TEMPORAL_VERSION, VISIBILITY_VERSION, SCENE_VERSION, REFLECTIONS_VERSION, INITIAL_DARKENING_VERSION, SIDEBAR_DARKENING_VERSION, COHERENCE_VERSION, SECTION_VERSION, 'end4-live-0.6.4-r34', 'end4-live-0.6.4-r33', 'end4-live-0.6.4-r32', 'end4-live-0.6.4-r31', 'end4-live-0.6.4-r30', 'end4-live-0.6.4-r29', 'end4-live-0.6.4-r28', 'end4-live-0.6.4-r27', 'end4-live-0.6.4-r26', 'end4-live-0.6.4-r25', 'end4-live-0.6.4-r24', 'end4-live-0.6.4-r23', 'end4-live-0.6.4-r22', 'end4-live-0.6.4-r21', 'end4-live-0.6.4-r20', 'end4-live-0.6.4-r19', FADE_VERSION), 'windowFrosted': plugin.get('version') in (VERSION, CANDIDATE_VERSION, TEMPORAL_VERSION, PREVIOUS_TEMPORAL_VERSION, VISIBILITY_VERSION, SCENE_VERSION, REFLECTIONS_VERSION, INITIAL_DARKENING_VERSION, SIDEBAR_DARKENING_VERSION, COHERENCE_VERSION, SECTION_VERSION, 'end4-live-0.6.4-r34', 'end4-live-0.6.4-r33', 'end4-live-0.6.4-r32', 'end4-live-0.6.4-r31', 'end4-live-0.6.4-r30', 'end4-live-0.6.4-r29', 'end4-live-0.6.4-r28', 'end4-live-0.6.4-r27', 'end4-live-0.6.4-r26', 'end4-live-0.6.4-r25', 'end4-live-0.6.4-r24', 'end4-live-0.6.4-r23', 'end4-live-0.6.4-r22', 'end4-live-0.6.4-r21', FADE_VERSION), 'contrast': plugin.get('version') in (VERSION, CANDIDATE_VERSION, TEMPORAL_VERSION, PREVIOUS_TEMPORAL_VERSION, VISIBILITY_VERSION, SCENE_VERSION, REFLECTIONS_VERSION, INITIAL_DARKENING_VERSION, SIDEBAR_DARKENING_VERSION, COHERENCE_VERSION, SECTION_VERSION, 'end4-live-0.6.4-r34', 'end4-live-0.6.4-r33', 'end4-live-0.6.4-r32', 'end4-live-0.6.4-r31', 'end4-live-0.6.4-r30', 'end4-live-0.6.4-r29', 'end4-live-0.6.4-r28', 'end4-live-0.6.4-r27', 'end4-live-0.6.4-r26', 'end4-live-0.6.4-r25', 'end4-live-0.6.4-r24', 'end4-live-0.6.4-r23', 'end4-live-0.6.4-r22', 'end4-live-0.6.4-r21', 'end4-live-0.6.4-r20', 'end4-live-0.6.4-r19', 'end4-live-0.6.4-r18', 'end4-live-0.6.4-r17', FADE_VERSION), 'frosted': plugin.get('version') in (VERSION, CANDIDATE_VERSION, TEMPORAL_VERSION, PREVIOUS_TEMPORAL_VERSION, VISIBILITY_VERSION, SCENE_VERSION, REFLECTIONS_VERSION, INITIAL_DARKENING_VERSION, SIDEBAR_DARKENING_VERSION, COHERENCE_VERSION, SECTION_VERSION, 'end4-live-0.6.4-r34', 'end4-live-0.6.4-r33', 'end4-live-0.6.4-r32', 'end4-live-0.6.4-r31', 'end4-live-0.6.4-r30', 'end4-live-0.6.4-r29', 'end4-live-0.6.4-r28', 'end4-live-0.6.4-r27', 'end4-live-0.6.4-r26', 'end4-live-0.6.4-r25', 'end4-live-0.6.4-r24', 'end4-live-0.6.4-r23', 'end4-live-0.6.4-r22', 'end4-live-0.6.4-r21', 'end4-live-0.6.4-r20', 'end4-live-0.6.4-r19', 'end4-live-0.6.4-r18', 'end4-live-0.6.4-r17', 'end4-live-0.6.4-r16', 'end4-live-0.6.4-r15', 'end4-live-0.6.4-r14', 'end4-live-0.6.4-r13', 'end4-live-0.6.4-r12', 'end4-live-0.6.4-r10', FADE_VERSION), 'enhanced': plugin.get('version') in (VERSION, CANDIDATE_VERSION, TEMPORAL_VERSION, PREVIOUS_TEMPORAL_VERSION, VISIBILITY_VERSION, SCENE_VERSION, REFLECTIONS_VERSION, INITIAL_DARKENING_VERSION, SIDEBAR_DARKENING_VERSION, COHERENCE_VERSION, SECTION_VERSION, 'end4-live-0.6.4-r34', 'end4-live-0.6.4-r33', 'end4-live-0.6.4-r32', 'end4-live-0.6.4-r31', 'end4-live-0.6.4-r30', 'end4-live-0.6.4-r29', 'end4-live-0.6.4-r28', 'end4-live-0.6.4-r27', 'end4-live-0.6.4-r26', 'end4-live-0.6.4-r25', 'end4-live-0.6.4-r24', 'end4-live-0.6.4-r23', 'end4-live-0.6.4-r22', 'end4-live-0.6.4-r21', 'end4-live-0.6.4-r20', 'end4-live-0.6.4-r19', 'end4-live-0.6.4-r18', 'end4-live-0.6.4-r17', 'end4-live-0.6.4-r16', 'end4-live-0.6.4-r15', 'end4-live-0.6.4-r14', 'end4-live-0.6.4-r13', 'end4-live-0.6.4-r12', 'end4-live-0.6.4-r11', 'end4-live-0.6.4-r10', 'end4-live-0.6.4-r9', 'end4-live-0.6.4-r8', 'end4-live-0.6.4-r7', 'end4-live-0.6.4-r6', 'end4-live-0.6.4-r5', 'end4-live-0.6.4-r4', FADE_VERSION), 'reason': '', 'lua': query('eval', 'return true') == 'ok'}
    directory = install_directory()
    binary, manifest = directory / 'hyprglass.so', directory / 'manifest.json'
    ticket = directory / 'test-once.json'
    once = ticket.is_file()
    if once:
        if not ensure:
            return {'available': False, 'reason': 'One-session test is pending'}
        if os.path.lexists(binary):
            return {'available': False, 'reason': 'Ordinary installation must remain absent during a one-session test'}
        manifest = ticket
        metadata = json.loads(ticket.read_text())
        if not isinstance(metadata, dict) or not isinstance(metadata.get('binary'), str) or not Path(metadata['binary']).is_absolute():
            return {'available': False, 'reason': 'Invalid one-session test ticket'}
        binary = Path(metadata['binary'])
        if metadata.get('testBoot') != boot_id():
            return {'available': False, 'reason': 'One-session test expired at reboot; plugin remains disabled'}
        if not metadata.get('deferInstance'):
            return {'available': False, 'reason': 'One-session test has no session exclusion'}
    if not ensure or not binary.is_file() or not manifest.is_file():
        return {'available': False, 'reason': 'Native glass is not installed'}
    metadata = json.loads(manifest.read_text())
    if not isinstance(metadata, dict):
        return {'available': False, 'reason': 'Invalid native glass manifest'}
    instance = os.environ.get('HYPRLAND_INSTANCE_SIGNATURE')
    if metadata.get('deferInstance') and (not instance or metadata['deferInstance'] == instance):
        return {'available': False, 'reason': 'Native glass is prepared for the next Hyprland session'}
    running = json.loads(query('version', '-j'))
    if metadata.get('abiHash') != running.get('abiHash') or not metadata.get('abiHash'):
        return {'available': False, 'reason': 'Rebuild native glass for this Hyprland version'}
    if metadata.get('sha256') != hashlib.sha256(binary.read_bytes()).hexdigest():
        return {'available': False, 'reason': 'Native glass binary does not match its manifest'}
    if once:
        consumed = directory / ('test-used-' + uuid.UUID(metadata['testId']).hex + '.json')
        if consumed.exists():
            return {'available': False, 'reason': 'One-session test was already consumed'}
        # Consume and persist BEFORE entering plugin/driver code. No success/crash cleanup is needed.
        os.rename(ticket, consumed)
        sync_directory(directory)
    # This build defaults to disabled: loading cannot glass unrelated application windows.
    result = query('plugin', 'load', str(binary))
    if result != 'ok':
        return {'available': False, 'reason': result}
    return status()


if __name__ == '__main__':
    try:
        if len(sys.argv) == 3 and sys.argv[1] == '--arm-once':
            result = arm_once(sys.argv[2])
        elif sys.argv[1:] == ['--cancel-once']:
            result = cancel_once()
        elif sys.argv[1:] in ([], ['--ensure']):
            result = status('--ensure' in sys.argv[1:])
        else:
            raise ValueError('Usage: backend.py [--ensure | --arm-once STAGING_DIRECTORY | --cancel-once]')
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        result = {'available': False, 'reason': str(error)}
    print(json.dumps(result))
