"""Probe/load only the ABI-matched end4 HyprGlass build installed by the user."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

VERSION = 'end4-live-0.6.4-r35'


def query(*args):
    result = subprocess.run(['hyprctl', *args], capture_output=True, text=True, timeout=10, check=True)
    return result.stdout.strip()


def status(ensure=False):
    plugins = json.loads(query('plugin', 'list', '-j'))
    plugin = next((p for p in plugins if p.get('name') == 'hyprglass'), None)
    if plugin:
        # The previous build may remain mapped until the current session exits.
        if plugin.get('version') not in (VERSION, 'end4-live-0.6.4-r34', 'end4-live-0.6.4-r33', 'end4-live-0.6.4-r32', 'end4-live-0.6.4-r31', 'end4-live-0.6.4-r30', 'end4-live-0.6.4-r29', 'end4-live-0.6.4-r28', 'end4-live-0.6.4-r27', 'end4-live-0.6.4-r26', 'end4-live-0.6.4-r25', 'end4-live-0.6.4-r24', 'end4-live-0.6.4-r23', 'end4-live-0.6.4-r22', 'end4-live-0.6.4-r21', 'end4-live-0.6.4-r20', 'end4-live-0.6.4-r19', 'end4-live-0.6.4-r18', 'end4-live-0.6.4-r17', 'end4-live-0.6.4-r16', 'end4-live-0.6.4-r15', 'end4-live-0.6.4-r14', 'end4-live-0.6.4-r13', 'end4-live-0.6.4-r12', 'end4-live-0.6.4-r11', 'end4-live-0.6.4-r10', 'end4-live-0.6.4-r9', 'end4-live-0.6.4-r8', 'end4-live-0.6.4-r7', 'end4-live-0.6.4-r6', 'end4-live-0.6.4-r5', 'end4-live-0.6.4-r4', 'end4-live-0.6.4-r3', 'end4-live-0.6.4-r2'):
            return {'available': False, 'reason': 'A different HyprGlass build is loaded'}
        # Keep existing capabilities while r34 awaits the next login; negotiate darkening separately.
        return {'available': True, 'uniformDarkening': plugin.get('version') in (VERSION, 'end4-live-0.6.4-r34', 'end4-live-0.6.4-r33', 'end4-live-0.6.4-r32', 'end4-live-0.6.4-r31', 'end4-live-0.6.4-r30', 'end4-live-0.6.4-r29'), 'darkening': plugin.get('version') in (VERSION, 'end4-live-0.6.4-r34', 'end4-live-0.6.4-r33', 'end4-live-0.6.4-r32', 'end4-live-0.6.4-r31', 'end4-live-0.6.4-r30', 'end4-live-0.6.4-r29', 'end4-live-0.6.4-r28', 'end4-live-0.6.4-r27'), 'barVisibility': plugin.get('version') in (VERSION, 'end4-live-0.6.4-r34', 'end4-live-0.6.4-r33', 'end4-live-0.6.4-r32', 'end4-live-0.6.4-r31', 'end4-live-0.6.4-r30', 'end4-live-0.6.4-r29', 'end4-live-0.6.4-r28', 'end4-live-0.6.4-r27', 'end4-live-0.6.4-r26'), 'profiles': plugin.get('version') in (VERSION, 'end4-live-0.6.4-r34', 'end4-live-0.6.4-r33', 'end4-live-0.6.4-r32', 'end4-live-0.6.4-r31', 'end4-live-0.6.4-r30', 'end4-live-0.6.4-r29', 'end4-live-0.6.4-r28', 'end4-live-0.6.4-r27', 'end4-live-0.6.4-r26', 'end4-live-0.6.4-r25', 'end4-live-0.6.4-r24', 'end4-live-0.6.4-r23', 'end4-live-0.6.4-r22', 'end4-live-0.6.4-r21'), 'topBarOptics': plugin.get('version') in (VERSION, 'end4-live-0.6.4-r34', 'end4-live-0.6.4-r33', 'end4-live-0.6.4-r32', 'end4-live-0.6.4-r31', 'end4-live-0.6.4-r30', 'end4-live-0.6.4-r29', 'end4-live-0.6.4-r28', 'end4-live-0.6.4-r27', 'end4-live-0.6.4-r26', 'end4-live-0.6.4-r25', 'end4-live-0.6.4-r24', 'end4-live-0.6.4-r23', 'end4-live-0.6.4-r22', 'end4-live-0.6.4-r21', 'end4-live-0.6.4-r20', 'end4-live-0.6.4-r19'), 'windowFrosted': plugin.get('version') in (VERSION, 'end4-live-0.6.4-r34', 'end4-live-0.6.4-r33', 'end4-live-0.6.4-r32', 'end4-live-0.6.4-r31', 'end4-live-0.6.4-r30', 'end4-live-0.6.4-r29', 'end4-live-0.6.4-r28', 'end4-live-0.6.4-r27', 'end4-live-0.6.4-r26', 'end4-live-0.6.4-r25', 'end4-live-0.6.4-r24', 'end4-live-0.6.4-r23', 'end4-live-0.6.4-r22', 'end4-live-0.6.4-r21'), 'contrast': plugin.get('version') in (VERSION, 'end4-live-0.6.4-r34', 'end4-live-0.6.4-r33', 'end4-live-0.6.4-r32', 'end4-live-0.6.4-r31', 'end4-live-0.6.4-r30', 'end4-live-0.6.4-r29', 'end4-live-0.6.4-r28', 'end4-live-0.6.4-r27', 'end4-live-0.6.4-r26', 'end4-live-0.6.4-r25', 'end4-live-0.6.4-r24', 'end4-live-0.6.4-r23', 'end4-live-0.6.4-r22', 'end4-live-0.6.4-r21', 'end4-live-0.6.4-r20', 'end4-live-0.6.4-r19', 'end4-live-0.6.4-r18', 'end4-live-0.6.4-r17'), 'frosted': plugin.get('version') in (VERSION, 'end4-live-0.6.4-r34', 'end4-live-0.6.4-r33', 'end4-live-0.6.4-r32', 'end4-live-0.6.4-r31', 'end4-live-0.6.4-r30', 'end4-live-0.6.4-r29', 'end4-live-0.6.4-r28', 'end4-live-0.6.4-r27', 'end4-live-0.6.4-r26', 'end4-live-0.6.4-r25', 'end4-live-0.6.4-r24', 'end4-live-0.6.4-r23', 'end4-live-0.6.4-r22', 'end4-live-0.6.4-r21', 'end4-live-0.6.4-r20', 'end4-live-0.6.4-r19', 'end4-live-0.6.4-r18', 'end4-live-0.6.4-r17', 'end4-live-0.6.4-r16', 'end4-live-0.6.4-r15', 'end4-live-0.6.4-r14', 'end4-live-0.6.4-r13', 'end4-live-0.6.4-r12', 'end4-live-0.6.4-r10'), 'enhanced': plugin.get('version') in (VERSION, 'end4-live-0.6.4-r34', 'end4-live-0.6.4-r33', 'end4-live-0.6.4-r32', 'end4-live-0.6.4-r31', 'end4-live-0.6.4-r30', 'end4-live-0.6.4-r29', 'end4-live-0.6.4-r28', 'end4-live-0.6.4-r27', 'end4-live-0.6.4-r26', 'end4-live-0.6.4-r25', 'end4-live-0.6.4-r24', 'end4-live-0.6.4-r23', 'end4-live-0.6.4-r22', 'end4-live-0.6.4-r21', 'end4-live-0.6.4-r20', 'end4-live-0.6.4-r19', 'end4-live-0.6.4-r18', 'end4-live-0.6.4-r17', 'end4-live-0.6.4-r16', 'end4-live-0.6.4-r15', 'end4-live-0.6.4-r14', 'end4-live-0.6.4-r13', 'end4-live-0.6.4-r12', 'end4-live-0.6.4-r11', 'end4-live-0.6.4-r10', 'end4-live-0.6.4-r9', 'end4-live-0.6.4-r8', 'end4-live-0.6.4-r7', 'end4-live-0.6.4-r6', 'end4-live-0.6.4-r5', 'end4-live-0.6.4-r4'), 'reason': '', 'lua': query('eval', 'return true') == 'ok'}
    directory = Path(os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local/share'))) / 'end4-pC/native-glass'
    binary, manifest = directory / 'hyprglass.so', directory / 'manifest.json'
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
    # This build defaults to disabled: loading cannot glass unrelated application windows.
    result = query('plugin', 'load', str(binary))
    if result != 'ok':
        return {'available': False, 'reason': result}
    return status()


if __name__ == '__main__':
    try:
        result = status('--ensure' in sys.argv[1:])
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        result = {'available': False, 'reason': str(error)}
    print(json.dumps(result))
