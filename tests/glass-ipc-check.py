"""Run: python3 tests/glass-ipc-check.py. Local sockets, offscreen Qt, no compositor/GPU calls.

Reproduce Hyprland v0.55.4's blocking 1023-byte read loop with the real QML senders.
"""
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import tempfile
import threading

source = (Path(__file__).resolve().parents[1] / 'services/GlassCompositor.qml').read_text()
framing = re.search(r'    function ipcRequest\([\s\S]*?\n    \}', source)[0]
geometry = 'end4glass 42 2 1 quickshell:settings eDP-1 900 600 0'
profiles = 'end4profiles 42 1 0'


def check(sender, command, legacy=False):
    with tempfile.TemporaryDirectory(prefix='glass-ipc-', dir='/tmp') as directory:
        base = Path(directory)
        env = {**os.environ, 'QT_QPA_PLATFORM': 'offscreen', 'QT_QUICK_BACKEND': 'software',
               'QT_QPA_PLATFORMTHEME': '', 'QS_DISABLE_COMPOSITOR_GLASS': '1',
               'HYPRLAND_INSTANCE_SIGNATURE': 'test'}
        env.pop('WAYLAND_DISPLAY', None)
        for kind in ('CONFIG', 'STATE', 'CACHE', 'DATA', 'RUNTIME'):
            path = base / kind.lower()
            path.mkdir(mode=0o700)
            env['XDG_' + kind + ('_DIR' if kind == 'RUNTIME' else '_HOME')] = str(path)
        ipc = base / 'runtime/hypr/test/.socket.sock'
        ipc.parent.mkdir(parents=True)
        listener = socket.socket(socket.AF_UNIX)
        listener.bind(str(ipc))
        listener.listen(1)
        listener.settimeout(5)
        received = bytearray()
        errors = []
        blocked = []

        def reply():
            try:
                with listener, listener.accept()[0] as connection:
                    connection.settimeout(.75)  # Bound the mock; never hang the real compositor.
                    try:
                        while True:
                            chunk = connection.recv(1023)
                            received.extend(chunk)
                            if len(chunk) < 1023:
                                break
                    except TimeoutError:
                        blocked.append(True)
                    connection.sendall(b'error\n' if blocked else b'ok\n')
            except Exception as error:
                errors.append(repr(error))

        worker = threading.Thread(target=reply, daemon=True)
        worker.start()
        actual = re.search(r'    Socket \{\n        id: ' + sender + r'Socket\n[\s\S]*?\n    \}', source)[0]
        helper = 'function ipcRequest(command) { return "/" + command }' if legacy else framing
        qml = '''import QtQuick
import Quickshell
import Quickshell.Io
ShellRoot {
    id: root
    property string regionsSent: COMMAND
    property string profilesSent: COMMAND
    property string regionsApplied: ""
    property string profilesApplied: ""
    property string regionsRejected: ""
    property bool regionsBusy: true
    property bool profilesBusy: true
    function queueRegions() { finish(regionsApplied === regionsSent) }
    function sendProfiles() { finish(profilesApplied === profilesSent) }
    function finish(ok) { console.log("IPC RESULT " + ok); Qt.quit() }
    HELPER
    SOCKET
    Component.onCompleted: SENDER.connected = true
    Timer { interval: 3000; running: true; onTriggered: { console.error("IPC DEADLINE"); Qt.quit() } }
}
'''
        if sender == 'profiles':
            actual = 'QtObject { id: regionSocket; property string path: ' + json.dumps(str(ipc)) + ' }\n' + actual
        shell = base / 'shell.qml'
        shell.write_text(qml.replace('COMMAND', json.dumps(command)).replace('HELPER', helper)
                         .replace('SOCKET', actual).replace('SENDER', sender + 'Socket'))
        result = subprocess.run(['qs', '--no-color', '-p', str(shell)], env=env,
                                capture_output=True, text=True, timeout=8)
        worker.join(timeout=6)
        output = result.stdout + result.stderr
        assert not worker.is_alive() and not errors, errors
        assert result.returncode == 0 and 'IPC RESULT ' + str(not legacy).lower() in output, output
        assert bool(blocked) == legacy, (sender, len(received), output)
        wire = b'/' + command.encode()
        assert bytes(received) == wire + (b' ' if not legacy and len(wire) % 1023 == 0 else b'')


# The old client must actually stall the bounded mock at a full block.
check('region', geometry + ' ' * (1023 - len(('/' + geometry).encode())), legacy=True)
for sender, command in [('region', geometry), ('profiles', profiles)]:
    for size in (1022, 1023, 1024, 2045, 2046, 3069):
        check(sender, command + ' ' * (size - len(('/' + command).encode())))
unicode_geometry = geometry.replace('eDP-1', 'écran🎵')
check('region', unicode_geometry + ' ' * (1023 - len(('/' + unicode_geometry).encode())))
check('region', geometry + ' ' * (32736 - len(('/' + geometry).encode())))
print('Glassy IPC: old full-block stall reproduced; real QML geometry/profile senders pass boundaries, UTF-8 and large requests offscreen.')
