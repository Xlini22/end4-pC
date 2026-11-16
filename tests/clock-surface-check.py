"""Run: python3 tests/clock-surface-check.py --plugin PATH_TO_MATCHED_HYPRGLASS.
Checks a real small clock surface in an isolated compositor; Qt paints on the CPU.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

repo = Path(__file__).resolve().parents[1]
fixture = repo / 'tests/native-glass-motion-check.py'
qml = '''//@ pragma UseQApplication
//@ pragma Env QT_QUICK_CONTROLS_STYLE=Basic
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import qs
import qs.services
import qs.modules.common
import qs.modules.common.widgets.widgetCanvas
import qs.modules.ii.background.widgets.clock
ShellRoot {
    FloatingWindow { id: coverWindow; visible: false; surfaceFormat.opaque: true; width: 900; height: 700; color: "#123456"; title: "clock-cover" }
    FloatingWindow { id: transparentCover; visible: false; width: 900; height: 700; color: "#40123456"; title: "clock-transparent" }
    PanelWindow {
        id: pane
        anchors { top: true; left: true; bottom: true; right: true }
        exclusionMode: ExclusionMode.Ignore
        WlrLayershell.namespace: "end4-clock-check-canvas"
        WlrLayershell.layer: WlrLayer.Bottom
        color: "#123456"
        WidgetCanvas {
            id: canvas
            width: pane.width; height: pane.height
            Rectangle { id: wallpaper; width: canvas.width; height: canvas.height; color: "#123456" }
            Item {
                width: clock.implicitWidth; height: clock.implicitHeight
                WindowedClock {
                    id: clock
                    canvas: canvas
                    screenWidth: pane.width; screenHeight: pane.height
                    scaledScreenWidth: pane.width; scaledScreenHeight: pane.height
                    wallpaperScale: 1
                    wallpaperItem: wallpaper
                    animateXPos: false; animateYPos: false
                }
            }
            Item { id: obstacle; visible: false; x: clock.x; y: clock.y; width: clock.width; height: clock.height; z: 1000 }
        }
    }
    Timer {
        interval: 50; running: true; repeat: true
        onTriggered: {
            if (!Config.ready) return;
            Config.blockWrites = true;
            Config.options.background.widgets.clock.placementStrategy = "free";
            Config.options.background.widgets.clock.style = "cookie";
            Config.options.background.widgets.clock.styleLocked = "cookie";
            Config.options.background.widgets.clock.cookie.constantlyRotate = true;
            Config.options.background.widgets.clock.cookie.aiStyling = false;
            Config.options.background.widgets.clock.x = 160;
            Config.options.background.widgets.clock.y = 120;
            Config.options.background.widgets.blurWidgets = false;
            Config.options.time.secondPrecision = false;
            canvas.registerWidget(obstacle);
            running = false;
        }
    }
    function face(item) {
        if (item.clockSecond !== undefined && item.useSineCookie !== undefined) return item.children[0];
        for (const child of item.children ?? []) { const result = face(child); if (result) return result; }
        return null;
    }
    IpcHandler {
        target: "clock-check"
        function state(): string {
            return JSON.stringify({detached: clock.detached, x: clock.x, y: clock.y,
                w: clock.width, h: clock.height, cx: canvas.x, cy: canvas.y,
                registered: canvas.registeredWidgets.includes(clock), controller: clock.findCanvas(clock.parent) === canvas,
                phase: face(clock)?.rotation, locked: GlobalStates.screenLocked, paused: clock.rotationPaused, visibility: GlassCompositor.clockVisibility});
        }
        function move(x: real, y: real): void { Config.options.background.widgets.clock.x=x; Config.options.background.widgets.clock.y=y; }
        function pan(x: real, y: real): void { canvas.x=x; canvas.y=y; }
        function overlap(value: bool): void { obstacle.visible=value; }
        function blur(value: bool): void { Config.options.background.widgets.blurWidgets=value; }
        function locked(value: bool): void { GlobalStates.screenLocked=value; }
        function save(): void { clock.commitPosition(); }
        function cover(value: bool): void { coverWindow.visible=value; transparentCover.visible=false; }
        function transparent(value: bool): void { coverWindow.visible=!value; transparentCover.visible=value; }
    }
}
'''
source = fixture.read_text().split('plugins = json.loads(control(', 1)[0]
source = source.replace("(shell / 'shell.qml').write_text(FIXTURE)", "(shell / 'shell.qml').write_text(CLOCK)")
source = source.replace("nested_env['QT_QPA_PLATFORM'] = 'wayland'", "nested_env['QT_QPA_PLATFORM'] = 'wayland'\n    nested_env['QT_QUICK_BACKEND'] = 'software'")
scope = {'__file__': str(fixture), '__name__': '__main__', 'CLOCK': qml}
try:
    exec(compile(source, str(fixture), 'exec'), scope)
    env, shell = scope['nested_env'], scope['shell']

    def ipc(function, *args):
        return subprocess.check_output(['qs', '-p', str(shell / 'shell.qml'), 'ipc', 'call', 'clock-check', function, *map(str, args)], env=env, text=True, timeout=5).strip()

    def expect(detached):
        deadline = time.monotonic() + 12
        while time.monotonic() < deadline:
            try:
                state = json.loads(ipc('state'))
                if state['detached'] is detached and state['registered'] and state['controller']:
                    return state
            except (ValueError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
                pass
            time.sleep(.1)
        raise AssertionError((scope['base'] / 'fixture.log').read_text())

    def bounds(state):
        layers = json.loads(scope['control']('layers', '-j'))
        found = [layer for monitor in layers.values() for level in monitor['levels'].values()
                 for layer in level if layer.get('namespace') == 'end4-background-clock' and layer['pid'] > 0]
        assert len(found) == 1, found
        layer = found[0]
        assert abs(layer['x'] - (state['x'] + state['cx'] - 32)) <= 1, (layer, state)
        assert abs(layer['y'] - (state['y'] + state['cy'] - 32)) <= 1, (layer, state)
        assert state['w'] + 64 <= layer['w'] <= state['w'] + 66, (layer, state)
        assert state['h'] + 64 <= layer['h'] <= state['h'] + 66, (layer, state)
        assert layer['w'] < 500 and layer['h'] < 500, layer

    state = expect(True)
    time.sleep(.5)
    state = expect(True)
    bounds(state)
    phase = state['phase']
    time.sleep(.3)
    assert abs(expect(True)['phase'] - phase) > .5, 'Clock rotation stopped'
    ipc('move', 250, 210)
    ipc('pan', -8, 5)
    time.sleep(.4)
    state = expect(True)
    bounds(state)
    assert abs(state['x'] - 250) < 1 and abs(state['y'] - 210) < 1, state
    ipc('save')
    bounds(expect(True))
    for function in ('overlap', 'blur', 'locked'):
        ipc(function, 'true')
        expect(False)
        ipc(function, 'false')
        time.sleep(.3)
        bounds(expect(True))
    def paused(wanted):
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            state = expect(True)
            if state['paused'] is wanted: return state
            time.sleep(.1)
        raise AssertionError(('Clock occlusion state did not change', state, scope['control']('clients','-j'), (scope['base']/'fixture.log').read_text()[-2500:]))

    ipc('cover', 'true')
    phase = paused(True)['phase']
    time.sleep(.4)
    assert abs(paused(True)['phase'] - phase) < .1, 'Covered clock still animates'
    ipc('transparent', 'true')
    phase = paused(False)['phase']
    time.sleep(.4)
    assert abs(paused(False)['phase'] - phase) > .5, 'Clock froze behind a transparent window'
    ipc('transparent', 'false')
    paused(True)
    clients = json.loads(scope['control']('clients', '-j'))
    address = 'address:' + next(c['address'] for c in clients if c['title'] == 'clock-cover')
    scope['control']('dispatch', 'setfloating', address)
    scope['control']('dispatch', 'resizewindowpixel', 'exact 350 350,' + address)
    scope['control']('dispatch', 'movewindowpixel', 'exact 300 210,' + address)
    paused(False)
    ipc('cover', 'false')
    phase = paused(False)['phase']
    time.sleep(.4)
    assert abs(paused(False)['phase'] - phase) > .5, 'Visible clock did not resume'
    log = (scope['base'] / 'fixture.log').read_text()
    assert not any(error in log for error in ('ReferenceError', 'TypeError', 'Binding loop', 'Cannot use same item on different windows', 'ShaderEffectSource: sourceItem')), log
    print('Small clock surface: geometry/controller/fallbacks; covered clock pauses, transparent/partial coverage and reveal resume rotation')
finally:
    if 'cleanup' in scope:
        scope['cleanup']()
