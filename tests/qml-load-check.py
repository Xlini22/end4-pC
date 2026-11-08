"""Run with python3 tests/qml-load-check.py in a Wayland session.
Compile the panel family and check settings scrolling without desktop windows.
"""
from pathlib import Path
import os
import json
import re
import socket
import threading
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
qml = '''//@ pragma UseQApplication
//@ pragma Env QT_QUICK_CONTROLS_STYLE=Basic
import QtQuick
import Quickshell
import Quickshell.Io
import qs.modules.common
import qs.services
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
    id: root
    property bool contrastActive: true
    property var contrastSamples: []
    property int contrastTick: 0
    property real dashboardScrollEnd: -1
    QtObject { id: regionSocket; property string path: SOCKET_PATH }
    CONTRAST_SOCKET
    CONTRAST_VALIDATION
    Component.onCompleted: contrastSocket.connected = true
    Timer {
        id: connectionFailure
        interval: 200
        onTriggered: {
            if (root.contrastSamples.length !== 0) throw new Error("IPC failure must clear stale contrast data")
            const areas = []
            collectScrollAreas(dashboardSettings, areas)
            if (Math.abs(areas.find(item => item.visible && item.enabled).flickable.contentY - root.dashboardScrollEnd) > .00001)
                throw new Error("Dashboard navigation animation resumed after direct touchpad input")
            const card = recycledCard.item
            if (card.animScale <= .25 || card.animOpacity <= 0 || card.offsetX >= card.travelX)
                throw new Error("A scrolling tile's entrance animation did not advance")
            dashboardPager.pageExitRequested()
            animationCheck.start()
        }
    }
    Timer {
        id: animationCheck
        interval: 400
        onTriggered: {
            const card = recycledCard.item
            if (card.animOpacity !== 0 || Math.abs(card.offsetX - card.travelX) > .001)
                throw new Error("Animated tiles must also leave when the page changes")
            console.log("SYNC COMPONENT COMPILE PASSED")
            Qt.quit()
        }
    }
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
    Item {
        id: cardViewport
        width: 300; height: 100; clip: true
        property bool scrolling: false
        Widgets.DashboardCard { id: dashboardCard; width: 280; height: 140; tint: "#4080a0" }
        Loader { id: recycledCard; active: false; sourceComponent: Widgets.DashboardCard { width: 100; height: 80; travelX: 160; pager: dashboardPager } }
    }
    Widgets.ContentPage {
        id: scrollPage
        width: 800; height: 300
        Item { implicitWidth: 600; implicitHeight: 1600 }
    }
    Item {
        id: dashboardPager
        width: 900; height: 600
        property string searchQuery: ""
        signal pageExitRequested()
        Settings.DashboardSettingsPage { id: dashboardSettings; anchors.fill: parent; pager: dashboardPager }
    }
    function collectScrollAreas(item, result) {
        if (item.handleWheel !== undefined) result.push(item)
        for (const child of item.children ?? []) collectScrollAreas(child, result)
    }
    Timer {
        interval: 200; running: true
        onTriggered: {
            Config.options.background.widgets.glass.enable = false
            if (dashboardCard.color.a !== 1) throw new Error("Standard Dashboard cards must retain their tint")
            Config.options.background.widgets.glass.enable = true
            const material = dashboardCard.children.find(item => item.nativeRegion !== undefined)
            GlassCompositor.windowFrostedAvailable = false
            if (material.live || dashboardCard.color.a !== 1)
                throw new Error("Quarantined Dashboard must use solid cards, without a wallpaper or screencopy fallback")
            GlassCompositor.windowFrostedAvailable = true
            if (!material || !material.live || material.frost < 8 || material.nativeClip !== cardViewport)
                throw new Error("Dashboard must use the shared clipped frosted material")
            if (Math.abs(dashboardCard.color.a - .72) > .01 || Math.abs(dashboardCard.color.r - 64/255) > .01)
                throw new Error("Frosted Dashboard must preserve card hue")
            Config.options.background.widgets.glass.enable = false
            GlassCompositor.windowFrostedAvailable = false
            if (dashboardCard.color.a !== 1) throw new Error("Disabling Glassy must restore solid cards")
            cardViewport.scrolling = true
            recycledCard.active = true
            if (recycledCard.item.animScale !== .25 || recycledCard.item.animOpacity !== 0
                || recycledCard.item.offsetX !== 160)
                throw new Error("Cards recreated during scrolling must retain their entrance animation")
            const areas = []
            collectScrollAreas(scrollPage, areas)
            for (const faster of [false, true, false]) {
                Config.options.interactions.scrolling.fasterTouchpadScroll = faster
                const active = areas.filter(item => item.visible && item.enabled)
                if (active.length !== 1) throw new Error("Settings must have one active touchpad handler")
                if (faster) continue
                const area = active[0], view = area.flickable
                view.contentY = 120
                for (const delta of [-1, -1, 1, 1]) {
                    const before = view.contentY
                    const event = {pixelDelta:{x:0, y:delta}, angleDelta:{x:0, y:12*delta}, accepted:false}
                    area.handleWheel(event)
                    if (!event.accepted || view.contentY !== before - delta || view.flicking)
                        throw new Error("Direct scrolling must follow small steps and reversals without a flick")
                }
                const before = view.contentY
                const notch = {pixelDelta:{x:0, y:0}, angleDelta:{x:0, y:120}, accepted:true}
                area.handleWheel(notch)
                if (notch.accepted || view.contentY !== before) throw new Error("Mouse wheel must stay native")
                area.handleWheel({pixelDelta:{x:0, y:0}, angleDelta:{x:0, y:0}, accepted:true})
                area.handleWheel({pixelDelta:{x:0, y:0}, angleDelta:{x:0, y:1}, accepted:false})
                if (Math.abs(view.contentY - (before - 1/12)) > 0.00001)
                    throw new Error("Fine angle steps must not be rounded away")
            }
            const dashboardAreas = []
            collectScrollAreas(dashboardSettings, dashboardAreas)
            const direct = dashboardAreas.filter(item => item.visible && item.enabled)
            if (direct.length !== 1) throw new Error("Dashboard must handle direct touchpad input in standard mode")
            const area = direct[0], view = area.flickable
            view.contentY = 120
            dashboardSettings.scrollBy(120)
            for (const delta of [-1, -1, 1, 1]) {
                const before = view.contentY
                const event = {pixelDelta:{x:0,y:delta},angleDelta:{x:0,y:12*delta},accepted:false}
                area.handleWheel(event)
                if (!event.accepted || Math.abs(view.contentY - before + delta) > .00001 || view.flicking)
                    throw new Error("Dashboard direct scrolling must cancel navigation animation and follow each small reversal")
            }
            root.dashboardScrollEnd = view.contentY
            if (root.contrastSamples.length !== 1) throw new Error("Normal IPC close discarded the contrast sample")
            contrastSocket.connected = true
            connectionFailure.start()
        }
    }
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
    compositor = (root / 'services/GlassCompositor.qml').read_text()
    actual_socket = re.search(r'    Socket \{\n        id: contrastSocket\n[\s\S]*?\n    \}', compositor)[0]
    validation = re.search(r'    function validContrast\([\s\S]*?\n    \}', compositor)[0]
    socket_path = str(temporary / 'contrast.sock')
    listener = socket.socket(socket.AF_UNIX)
    listener.bind(socket_path)
    listener.listen(1)
    sample = {'name': 'quickshell:settings', 'monitor': 'test', 'width': 800, 'height': 600,
              'rect': [0, 0, 800, 600], 'columns': 32, 'rows': 24, 'luma': [0] * 768}

    def reply_once():
        with listener:
            connection, _ = listener.accept()
            with connection:
                assert connection.makefile('rb').read(len(b'/end4contrast')) == b'/end4contrast'
                connection.sendall((json.dumps([sample]) + '\n').encode())
        # The second connection is refused, exercising the real error fallback.

    threading.Thread(target=reply_once, daemon=True).start()
    harness.write_text(qml.replace('CONTRAST_SOCKET', actual_socket)
                       .replace('CONTRAST_VALIDATION', validation)
                       .replace('SOCKET_PATH', json.dumps(socket_path)))
    try:
        result = subprocess.run(['qs', '--no-color', '-p', str(harness)], cwd=root,
                                env=env, capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired as error:
        raise AssertionError((error.stdout or b'').decode() + (error.stderr or b'').decode()) from error
    output = result.stdout + result.stderr
    assert result.returncode == 0 and 'SYNC COMPONENT COMPILE PASSED' in output, output
    assert 'Failed to load configuration' not in output, output
    print('Panel family, direct scrolling and contrast IPC retention/error fallback passed without GPU rendering')
