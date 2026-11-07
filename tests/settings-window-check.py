"""Run python3 tests/settings-window-check.py in Wayland.
Exercise the real settings window with isolated preferences and hardware rendering.
"""
import json
import os
from pathlib import Path
import subprocess
import tempfile

repo = Path(__file__).resolve().parents[1]
qml = '''//@ pragma UseQApplication
//@ pragma Env QT_QUICK_CONTROLS_STYLE=Basic
import QtQuick
import Quickshell
import qs
import qs.services
import qs.modules.common
import qs.modules.ii.settings as Settings
ShellRoot {
    id: root
    property int cycle: 0
    property int phase: 0
    property double deadline: Date.now() + 30000
    property double started: Date.now()
    property var content: null
    function fail(message) { console.error(message); Qt.quit() }
    function loadedPages(item, result) {
        if (item.modelData?.component && item.item) result.push(item.modelData.id)
        for (const child of item.children ?? []) loadedPages(child, result)
    }
    Settings.Settings {}
    Timer {
        interval: 120; repeat: true; running: Config.ready
        onTriggered: {
            if (Date.now() > root.deadline) return root.fail("Settings failed to become ready at cycle " + root.cycle + " phase " + root.phase)
            if (root.phase === 0) {
                if (GlobalStates.currentPageInstance) return root.fail("Settings page created before opening")
                if (Config.readWriteDelay === 0) return root.fail("Settings disabled config write debouncing")
                Config.options.background.widgets.glass.enable = root.cycle >= 3 && root.cycle < 9
                Config.options.background.widgets.glass.enhanced = root.cycle % 2 === 1
                Config.options.background.widgets.glass.source = root.cycle >= 6 ? "windows" : "wallpaper"
                root.started = Date.now()
                GlobalStates.settingsOpen = true
                root.phase = 1
            } else if (root.phase === 1) {
                const page = GlobalStates.currentPageInstance
                if (!page) return
                let content = page
                while (content && !(content.pages !== undefined && content.currentPage !== undefined)) content = content.parent
                if (!content) return root.fail("Cannot find settings content")
                const loaded = []
                root.loadedPages(content, loaded)
                if (loaded.length !== 1 || loaded[0] !== "quick") return root.fail("Unvisited pages loaded: " + loaded.join(","))
                console.log("SETTINGS OPEN", root.cycle, Date.now() - root.started)
                root.content = content
                if (root.cycle === 0) {
                    content.currentPage = content.pages.findIndex(page => page.id === "interface")
                    root.phase = 4
                } else root.phase = 2
            } else if (root.phase === 2) {
                GlobalStates.settingsOpen = false
                root.phase = 3
            } else if (root.phase === 4) {
                if (GlobalStates.currentPageInstance?.parent?.modelData?.id !== "interface") return
                const loaded = []
                root.loadedPages(root.content, loaded)
                if (loaded.length !== 2) return root.fail("Navigation loaded unrelated pages")
                root.content.showingProfile = true
                root.phase = 5
            } else if (root.phase === 5) {
                if (!String(GlobalStates.currentPageInstance?.parent?.source).endsWith("Profile.qml")) return
                root.content.showingProfile = false
                root.content.currentPage = 0
                root.phase = 2
            } else {
                if (GlobalStates.currentPageInstance) return root.fail("Closed settings retain their page/effects")
                root.content = null
                root.cycle++
                root.deadline = Date.now() + 10000
                if (root.cycle === 12) {
                    console.log("Settings window lifecycle passed")
                    Qt.quit()
                } else root.phase = 0
            }
        }
    }
}
'''
display = os.environ.get('WAYLAND_DISPLAY', 'wayland-1')
if not display.startswith('/'):
    display = str(Path(os.environ.get('XDG_RUNTIME_DIR', f'/run/user/{os.getuid()}')) / display)
with tempfile.TemporaryDirectory(prefix='qp-') as directory:
    temporary = Path(directory)
    env = {**os.environ, 'QT_QPA_PLATFORM': 'wayland', 'WAYLAND_DISPLAY': display,
           'QT_QPA_PLATFORMTHEME': '', 'QSG_RENDER_LOOP': 'threaded', 'QS_DISABLE_COMPOSITOR_GLASS': '1'}
    env.pop('QT_QUICK_BACKEND', None)
    for key in ('CONFIG', 'STATE', 'CACHE', 'DATA'):
        path = temporary / key.lower()
        path.mkdir()
        env['XDG_' + key + '_HOME'] = str(path)
    # Hyprland's signature leaves little room within the Unix socket path limit.
    runtime = temporary
    real_runtime = Path(os.environ.get('XDG_RUNTIME_DIR', f'/run/user/{os.getuid()}'))
    if (real_runtime / 'hypr').is_dir():
        (runtime / 'hypr').symlink_to(real_runtime / 'hypr', target_is_directory=True)
    env['XDG_RUNTIME_DIR'] = str(runtime)
    wallpaper = temporary / 'wallpaper.svg'
    wallpaper.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="320" height="180"><rect width="320" height="180" fill="#b3a6da"/></svg>')
    config = temporary / 'config/illogical-impulse'
    config.mkdir()
    (temporary / 'state/quickshell').mkdir()
    (temporary / 'state/quickshell/states.json').write_text('{}')
    (config / 'config.json').write_text(json.dumps({'background': {'wallpaperPath': str(wallpaper), 'widgets': {'glass': {'enable': True}}}}))
    # ponytail: link production components into an isolated config so test creation cannot reload the desktop.
    shell = temporary / 'shell'
    shell.mkdir()
    for name in ('assets', 'defaults', 'modules', 'panelFamilies', 'scripts', 'services', 'translations'):
        (shell / name).symlink_to(repo / name, target_is_directory=True)
    for component in repo.glob('*.qml'):
        if component.name != 'shell.qml':
            (shell / component.name).symlink_to(component)
    harness = shell / 'shell.qml'
    harness.write_text(qml)
    result = subprocess.run(['qs', '--no-color', '-p', str(harness)], cwd=repo,
                            env=env, capture_output=True, text=True, timeout=65)
    output = result.stdout + result.stderr
    assert result.returncode == 0 and 'Settings window lifecycle passed' in output, output
    assert not any(error in output for error in ('Cannot use same item on different windows', 'Failed to load configuration', 'TypeError:')), output
    print('Real settings: lazy pages, repeated open/close and all glass modes passed')
