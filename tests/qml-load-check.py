"""Run with python3 tests/qml-load-check.py in a Wayland session.
Compile the full panel family and custom screens without creating desktop windows.
"""
from pathlib import Path
import os
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
qml = '''//@ pragma UseQApplication
//@ pragma Env QT_QUICK_CONTROLS_STYLE=Basic
import QtQuick
import Quickshell
import qs.panelFamilies as Families
import qs.modules.ii.bar as Bar
import qs.modules.ii.settings as Settings
import qs.modules.ii.settings.pages as Pages
import qs.modules.ii.sidebarLeft as Left
import qs.modules.ii.sidebarRight as Right
import qs.modules.ii.overview as Overview
import qs.modules.ii.lock as Lock
import qs.modules.common.widgets as Widgets
ShellRoot {
    Component { Families.IllogicalImpulseFamily {} }
    Component { Bar.BarContent {} }
    Component { Bar.DynamicIsland {} }
    Component { Bar.Omdrop {} }
    Component { Settings.Settings {} }
    Component { Pages.Profile {} }
    Component { Left.SidebarLeftContent { scopeRoot: null } }
    Component { Right.SidebarRightContent {} }
    Component { Overview.Overview {} }
    Component { Lock.LockSurface {} }
    Component { Widgets.Player { player: null } }
    Timer { interval: 200; running: true; onTriggered: { console.log("SYNC COMPONENT COMPILE PASSED"); Qt.quit() } }
}
'''
display = os.environ.get('WAYLAND_DISPLAY', 'wayland-1')
if not display.startswith('/'):
    display = str(Path(os.environ.get('XDG_RUNTIME_DIR', f'/run/user/{os.getuid()}')) / display)
with tempfile.TemporaryDirectory(prefix='qml-load-check-') as directory:
    temporary = Path(directory)
    env = {**os.environ, 'QT_QPA_PLATFORM': 'wayland', 'WAYLAND_DISPLAY': display,
           'QT_QUICK_BACKEND': 'software', 'QT_QPA_PLATFORMTHEME': '', 'QS_DISABLE_COMPOSITOR_GLASS': '1'}
    for kind in ('CONFIG', 'STATE', 'CACHE', 'DATA'):
        path = temporary / kind.lower()
        path.mkdir()
        env['XDG_' + kind + '_HOME'] = str(path)
    runtime = temporary / 'runtime'
    runtime.mkdir(mode=0o700)
    env['XDG_RUNTIME_DIR'] = str(runtime)
    # ponytail: test-only QML stays outside the watched desktop configuration.
    shell = temporary / 'shell'
    shell.mkdir()
    for name in ('assets', 'defaults', 'modules', 'panelFamilies', 'scripts', 'services', 'translations'):
        (shell / name).symlink_to(root / name, target_is_directory=True)
    for component in root.glob('*.qml'):
        if component.name != 'shell.qml':
            (shell / component.name).symlink_to(component)
    harness = shell / 'shell.qml'
    harness.write_text(qml)
    result = subprocess.run(['qs', '--no-color', '-p', str(harness)], cwd=root,
                            env=env, capture_output=True, text=True, timeout=30)
    output = result.stdout + result.stderr
    assert result.returncode == 0 and 'SYNC COMPONENT COMPILE PASSED' in output, output
    assert 'Failed to load configuration' not in output, output
    print('Full panel family and custom QML components compile successfully')
