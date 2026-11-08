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
    property string contrastBackground: ""
    PanelWindow {
        visible: contrastBackground !== ""
        anchors { top: true; bottom: true; left: true; right: true }
        WlrLayershell.namespace: "end4:contrast-test"
        WlrLayershell.layer: WlrLayer.Bottom
        exclusiveZone: 0
        color: contrastBackground === "black" ? "black" : "white"
        Rectangle {
            visible: contrastBackground === "split" || contrastBackground === "vertical"
            width: contrastBackground === "split" ? parent.width * .27 : parent.width
            height: contrastBackground === "vertical" ? parent.height / 2 : parent.height
            color: "black"
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
    function rows(item, result) {
        if (item.nativeRegion !== undefined && item.parent?.isFirst !== undefined) result.push(item)
        for (const child of item.children ?? []) rows(child, result)
    }
    function labels(item, result) {
        if (item.adaptiveGlass && item.visible && item.text?.length > 0) {
            const box = item.mapToItem(null, Qt.rect(0, 0, item.width, item.height))
            const c = item.color, x = box.x + box.width / 2, y = box.y + box.height / 2
            let clipped = false
            for (let parent = item.parent; parent; parent = parent.parent) if (parent.clip) {
                const clip = parent.mapToItem(null, Qt.rect(0, 0, parent.width, parent.height))
                if (x < clip.x || y < clip.y || x >= clip.x + clip.width || y >= clip.y + clip.height) { clipped = true; break }
            }
            if (!clipped && box.x >= 0 && box.y >= 0 && box.x + box.width <= 950 && box.y + box.height <= 1023)
                result.push({text:item.text, x, y, ink:[c.r,c.g,c.b]})
        }
        for (const child of item.children ?? []) labels(child,result)
    }
    function viewport() { return GlobalStates.currentPageInstance ? find(GlobalStates.currentPageInstance, item => item.contentY !== undefined) : null }
    IpcHandler {
        target: "settings-check"
        function background(value: bool): void { red.visible = value; blue.visible = value }
        function open(force: bool): void {
            Config.options.background.widgets.glass.enhanced = true
            Config.options.background.widgets.glass.haze = 1
            if (force) GlassCompositor.frostedAvailable = true
            GlobalStates.settingsOpen = true
        }
        function contrast(value: string): void { contrastBackground = value }
        function scroll(): void { viewport().contentY += 160 }
        function burst(): void { for (let n=0;n<80;n++) viewport().contentY += 1 }
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
            const inks=[]
            if (pane) labels(pane,inks)
            const allRows=[]
            if (pane) rows(pane,allRows)
            const view=viewport()
            const box=view?.mapToItem(null, Qt.rect(0,0,view.width,view.height))
            const materials=allRows.map(item=>({live:item.live, satin:item.satinRow, frost:item.frost,
                track:item.trackGeometry, watches:item.ancestorGeometry.length, alpha:item.parent.color.a,
                region:item.nativeRegion()?.values}))
            return JSON.stringify({inks, samples:GlassCompositor.contrastSamples.length, contrast:GlassCompositor.contrastAvailable, rows:materials, viewport:box, writes:GlassCompositor.regionWrites,
                rejected:GlassCompositor.regionsRejected, native: GlassCompositor.active, frosted: GlassCompositor.frostedAvailable, regions: GlassCompositor.regionsApplied,
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
    time.sleep(.8)
    state=json.loads(ipc('state'))
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
    for _ in range(3):
        ipc('scroll')
        time.sleep(.35)
        state=json.loads(ipc('state'))
        assert state['rows'] and not state['rejected'], state
        assert all(r['live'] and r['satin'] and r['frost']>=8 and r['alpha']==0 for r in state['rows']),state['rows'][:2]
        assert all(not r['track'] and r['watches']==0 for r in state['rows']),state['rows'][:2]
        visible=[r['region'] for r in state['rows'] if r.get('region')]
        assert 0<len(visible)<len(state['rows']),state['rows'][:2]
        box=state['viewport']
        for r in visible:
            assert r[0]>=box['x']-1 and r[1]>=box['y']-1,(r,box)
            assert r[0]+r[2]<=box['x']+box['width']+1 and r[1]+r[3]<=box['y']+box['height']+1,(r,box)
        native=json.loads(control('end4glass'))
        assert native['regions']==len(visible)+3,(native,len(visible))
    before=state['writes']
    ipc('burst')
    time.sleep(.4)
    state=json.loads(ipc('state'))
    assert 1<=state['writes']-before<=2,('Scroll updates were not coalesced per frame',before,state)
    print('Visible satin rows:',len(visible),'of',len(state['rows']),'burst writes:',state['writes']-before,flush=True)
    if '--contrast' in sys.argv:
        # Native RGB never leaves the compositor; only its bounded luminance grid reaches QML.
        for mode in ('black', 'white', 'split', 'vertical', 'black'):
            ipc('contrast', mode)
            time.sleep(3)  # Allow two 1.25-second contrast polls, including asynchronous GPU completion.
            state = json.loads(ipc('state'))
            assert state['contrast'] and state['samples'] == 1, (mode, state)
            inks = state['inks']
            assert inks, (mode, state)
            if mode in ('black', 'white'):
                expected = [231/255,237/255,242/255] if mode == 'black' else [27/255,34/255,41/255]
                assert all(max(abs(v - e) for v,e in zip(ink['ink'],expected)) < .02 for ink in inks), (mode, inks)
            else:
                monitor = json.loads(control('monitors', '-j'))[0]
                axis = 'x' if mode == 'split' else 'y'
                boundary = monitor['width' if mode == 'split' else 'height'] * (.27 if mode == 'split' else .5)
                low = [i for i in inks if i[axis] < boundary - 45]
                high = [i for i in inks if i[axis] > boundary + 45]
                assert low and high, (mode, inks)
                assert all(min(i['ink']) > .9 for i in low), (mode, low)
                assert all(max(i['ink']) < .2 for i in high), (mode, high)
            print('Adaptive text:',mode,'labels:',len(inks),flush=True)
        before = state['writes']
        time.sleep(.8)
        state = json.loads(ipc('state'))
        assert state['writes'] == before, 'Contrast polling must not resend geometry'
    assert control('dispatch', 'exit') == 'ok'
    assert scope['processes'][0].wait(timeout=10) == 0
    print(f'Real native Settings: Interface navigation and {checks} control pixels passed across moves')
except Exception:
    if 'base' in scope:
        Path('/tmp/end4-rows-fixture.log').write_text((scope['base']/'fixture.log').read_text())
    raise
finally:
    if 'cleanup' in scope: scope['cleanup']()
