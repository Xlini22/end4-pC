"""Run in a Wayland session: python3 tests/session-lock-reload-check.py.
Locks only an isolated Hyprland, without Glassy; Qt renders on the CPU.
"""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

root = Path(__file__).resolve().parents[1]
source = (root / 'modules/common/panels/lock/LockScreen.qml').read_text()


def block(marker):
    start = source.index('    ' + marker + ' {')
    return source[start:source.index('\n    }', start) + 6]


# Exercise the production persistence, binding and request handler with real WlSessionLock.
handler = source.split('            function onScreenLockedChanged() {', 1)[1].split('\n            }', 1)[0]
properties = source[source.index('    property var savedWorkspaces:'):source.index('    PersistentProperties {')]
qml = '''import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
ShellRoot {
    QtObject { id: globals; property bool screenLocked: false; property bool startupLockPending: true }
    Scope {
        id: root
        STATE_PROPERTIES
        property Component sessionLockSurface: WlSessionLockSurface {
            Rectangle { anchors.fill: parent; color: "steelblue" }
        }
        QtObject { id: lockContext; function reset() {} function tryFingerUnlock() {} }
        PERSISTENCE
        Connections { target: globals; function onScreenLockedChanged() { HANDLER } }
        NATIVE_LOCK
        IpcHandler {
            target: "check"
            function request(value: bool): void { globals.screenLocked = value }
            function remember(): void { root.savedWorkspaces = ({test: 2}); root.pushedTargets = ({test: 3}) }
            function status(): string {
                return JSON.stringify({requested: globals.screenLocked, locked: lock.locked, secure: lock.secure,
                    saved: root.savedWorkspaces, targets: root.pushedTargets})
            }
        }
    }
}
'''.replace('STATE_PROPERTIES', properties).replace('PERSISTENCE', block('PersistentProperties')).replace('HANDLER', handler).replace('NATIVE_LOCK', block('WlSessionLock')).replace('GlobalStates.', 'globals.')
shell_source = (root / 'shell.qml').read_text()
family_source = (root / 'panelFamilies/IllogicalImpulseFamily.qml').read_text()
assert '\n    SessionLock.Lock {}' in shell_source and 'component: Lock {}' not in family_source, 'The lock must outlive the Config.ready loaders'

# Hyprland's signature also consumes the Unix socket's 108-byte path limit.
with tempfile.TemporaryDirectory(prefix='lk-', dir='/tmp') as directory:
    base = Path(directory)
    base.chmod(0o700)
    display = Path(os.environ.get('WAYLAND_DISPLAY', 'wayland-1'))
    if not display.is_absolute():
        display = Path(os.environ.get('XDG_RUNTIME_DIR', f'/run/user/{os.getuid()}')) / display
    env = {**os.environ, 'XDG_RUNTIME_DIR': directory, 'WAYLAND_DISPLAY': str(display),
           'HYPRLAND_NO_SD_VARS': '1', 'HYPRLAND_NO_SD_NOTIFY': '1',
           'QT_QPA_PLATFORM': 'wayland', 'QT_QUICK_BACKEND': 'software', 'QT_QPA_PLATFORMTHEME': ''}
    for key in ('HYPRLAND_INSTANCE_SIGNATURE', 'HYPRLAND_CONFIG', 'NOTIFY_SOCKET', 'WATCHDOG_PID', 'WATCHDOG_USEC'):
        env.pop(key, None)
    config = base / 'hyprland.lua'
    config.write_text('hl.monitor({output="",mode="640x480@60",position="auto",scale=1})\n'
                      'hl.config({misc={disable_hyprland_logo=true,disable_splash_rendering=true,disable_autoreload=true},animations={enabled=false}})\n')
    processes = []
    with (base / 'hypr.log').open('w') as hlog, (base / 'qs.log').open('w') as qlog:
        try:
            processes.append(subprocess.Popen(['Hyprland', '--config', str(config)], env=env, stdout=hlog, stderr=subprocess.STDOUT))
            for _ in range(100):
                sockets = list((base / 'hypr').glob('*/.socket.sock'))
                displays = [p for p in base.glob('wayland-*') if not p.name.endswith('.lock')]
                if sockets and displays:
                    break
                assert processes[0].poll() is None, (base / 'hypr.log').read_text()
                time.sleep(.1)
            assert sockets and displays, (base / 'hypr.log').read_text()
            env.update(HYPRLAND_INSTANCE_SIGNATURE=sockets[0].parent.name, WAYLAND_DISPLAY=str(displays[0]))
            assert env['HYPRLAND_INSTANCE_SIGNATURE'] != os.environ.get('HYPRLAND_INSTANCE_SIGNATURE')
            shell = base / 'shell.qml'
            shell.write_text(qml)
            processes.append(subprocess.Popen(['qs', '--no-color', '-p', str(shell)], env=env, stdout=qlog, stderr=subprocess.STDOUT))

            def ipc(function, *args):
                return subprocess.run(['qs', '-p', str(shell), 'ipc', 'call', 'check', function, *args],
                                      env=env, capture_output=True, text=True, timeout=3).stdout.strip()

            def expect(locked):
                deadline = time.monotonic() + 12
                while time.monotonic() < deadline:
                    log = (base / 'qs.log').read_text()
                    assert 'FATAL:' not in log and 'Quickshell has crashed' not in log, log
                    assert all(p.poll() is None for p in processes), log
                    try:
                        state = json.loads(ipc('status'))
                    except (ValueError, subprocess.TimeoutExpired):
                        state = {}
                    if all(state.get(key) is locked for key in ('requested', 'locked', 'secure')):
                        return state
                    time.sleep(.1)
                raise AssertionError(f'Lock state did not settle: {state}\n{log}')

            expect(False)
            ipc('request', 'true')
            expect(True)
            ipc('remember')
            for revision in range(3):
                shell.write_text(qml + f'\n// reload {revision}\n')
                deadline = time.monotonic() + 12
                while (base / 'qs.log').read_text().count('Configuration Loaded') < revision + 2:
                    assert time.monotonic() < deadline, (base / 'qs.log').read_text()
                    time.sleep(.1)
                state = expect(True)
                assert state['saved'] == {'test': 2} and state['targets'] == {'test': 3}, state
                ipc('request', 'false')
                expect(False)
                ipc('request', 'true')
                expect(True)
            ipc('request', 'false')
            expect(False)
            print('Session lock survives 3 reloads and unlock/relock cycles; workspace targets retained')
        finally:
            for process in reversed(processes):
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
