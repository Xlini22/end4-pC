"""Check real Settings controls and dragging in an isolated native compositor.
Run: python3 tests/native-settings-check.py --plugin /path/to/hyprglass.so
Use --reproduce-r11 only to bypass the quarantined material in a test compositor.
"""
import json
from pathlib import Path
import subprocess
import sys
import time
from PIL import Image

fixture = Path(__file__).with_name('native-glass-motion-check.py')
qml = '''//@ pragma UseQApplication
//@ pragma Env QT_QUICK_CONTROLS_STYLE=Basic
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import qs
import qs.services
import qs.modules.common
import qs.modules.common.widgets
import qs.modules.ii.settings as Settings
ShellRoot {
    // A fullscreen layer with a small bar reproduces the desktop's scissor-cache sequence.
    PanelWindow {
        anchors { top: true; bottom: true; left: true; right: true }
        exclusiveZone: 0
        color: "transparent"
        WlrLayershell.namespace: "quickshell:bar"
        WlrLayershell.layer: WlrLayer.Top
        Item {
            width: parent.width; height: 48
            WindowGlass { anchors.fill: parent; cardRadius: 20 }
        }
    }
    Settings.Settings {}
    Window { id: red; visible: true; title: "glass-red"; color: "#c62828"; width: 1000; height: 1100 }
    Window { id: blue; visible: true; title: "glass-blue"; color: "#1565c0"; width: 1000; height: 1100 }
    function find(item, predicate) {
        if (predicate(item)) return item
        for (const child of item.children ?? []) { const found = find(child, predicate); if (found) return found }
        return null
    }
    function content() {
        for (let item = GlobalStates.currentPageInstance; item; item = item.parent)
            if (item.pages !== undefined && item.currentPage !== undefined) return item
        return null
    }
    IpcHandler {
        target: "settings-check"
        function background(value: bool): void { red.visible = value; blue.visible = value }
        function open(force: bool): void {
            Config.options.background.widgets.glass.enhanced = true
            Config.options.background.widgets.glass.haze = 1
            if (force) GlassCompositor.frostedAvailable = true
            GlobalStates.settingsOpen = true
        }
        function navigate(): void { find(content(), item => item.buttonText === "Interface").click() }
        function move(dx: real, dy: real): void {
            let item = content()
            while (item && item.userMoved === undefined) item = item.parent
            const x = item.x, y = item.y
            item.userMoved = true; item.x = x + dx; item.y = y + dy
        }
        function state(): string {
            const pane = content()
            const controls = []
            if (pane) for (const name of ["Config file", "Reload"]) {
                const item = find(pane, item => item.buttonText === name || item.mainText === name)
                if (!item) continue
                const p = item.mapToItem(null, item.width / 2, 8)
                const c = item.buttonColor
                controls.push({name, x: p.x, y: p.y, rgb: [c.r, c.g, c.b].map(v => Math.round(v * 255))})
            }
            return JSON.stringify({native: GlassCompositor.active, frosted: GlassCompositor.frostedAvailable, regions: GlassCompositor.regionsApplied,
                ready: pane !== null, page: pane?.pages[pane.currentPage]?.id, controls})
        }
    }
}
'''

# ponytail: share the existing fixture's isolated compositor lifecycle; replace only its test shell.
source = fixture.read_text().split("if sys.argv[1] == '--plugin':\n    for attempt in range(150):", 1)[0]
needle = "(shell / 'shell.qml').write_text(FIXTURE)"
assert source.count(needle) == 1
source = source.replace(needle, "(shell / 'shell.qml').write_text(qml)")
scope = {'__file__': str(fixture), '__name__': '__main__', 'qml': qml}
try:
    exec(compile(source, str(fixture), 'exec'), scope)
    env, shell, base = (scope[name] for name in ('nested_env', 'shell', 'base'))

    def ipc(function, *args):
        return subprocess.check_output(['qs', '-p', str(shell / 'shell.qml'), 'ipc', 'call',
                                        'settings-check', function, *args], env=env, text=True, timeout=10).strip()

    for _ in range(100):
        state = json.loads(ipc('state'))
        if state['native']: break
        time.sleep(.1)
    assert state['native'], state
    ipc('background', 'false')
    time.sleep(.6)
    ipc('open', 'true' if '--reproduce-r11' in sys.argv else 'false')
    for _ in range(100):
        state = json.loads(ipc('state'))
        if state['ready']: break
        time.sleep(.1)
    assert state['ready'] and state['frosted'], state
    ipc('navigate')
    for _ in range(100):
        state = json.loads(ipc('state'))
        if state.get('page') == 'interface' and len(state['controls']) == 2: break
        time.sleep(.1)
    assert state.get('page') == 'interface' and len(state['controls']) == 2, (state, (base / 'fixture.log').read_text()[-4000:])
    print('Real settings regions:', state['regions'], flush=True)
    control = scope['control']
    assert control('dispatch', 'workspace', '2') == 'ok'
    checks = 0
    for dx, dy in ((0, 0), (16, 80), (-32, -40), (16, -40)):
        ipc('move', str(dx), str(dy))
        time.sleep(.5)
        for frame_number in range(3):
            state = json.loads(ipc('state'))
            path = base / 'settings-controls.png'
            subprocess.run(['grim', str(path)], env=env, check=True, timeout=10)
            with Image.open(path).convert('RGB') as frame:
                frame.save('/tmp/end4-real-settings-native.png')
                for item in state['controls']:
                    x, y = round(item['x']), round(item['y'])
                    assert 0 <= x < frame.width and 0 <= y < frame.height, item
                    actual = frame.getpixel((x, y))
                    assert max(abs(a - b) for a, b in zip(actual, item['rgb'])) <= 8, ('Control missing or detached', item, actual)
                    checks += 1
            time.sleep(.1)
    assert control('dispatch', 'exit') == 'ok'
    assert scope['processes'][0].wait(timeout=10) == 0
    print(f'Real native Settings: Interface navigation and {checks} control pixels passed across moves')
finally:
    if 'cleanup' in scope: scope['cleanup']()
