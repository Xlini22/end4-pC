"""Run python3 tests/popup-window-check.py in Wayland; opens a small test popup.
Exercise the production media popup with glass and the threaded hardware renderer.
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
import Quickshell.Wayland
import qs.services
import qs.modules.common
import qs.modules.common.widgets
import qs.modules.ii.bar
ShellRoot {
    id: root
    property bool shown: false
    property var firstWindow: null
    property var firstParent: null
    property int step: 0
    function fail(message) { console.error(message); Qt.quit() }
    function collectGlass(item, result) {
        if (item.glassEnabled !== undefined && item.cardRadius !== undefined) result.push(item)
        for (const child of item.children ?? []) collectGlass(child, result)
    }
    function findCapture(item) {
        if (item.sourceItem !== undefined && item.scheduleUpdate !== undefined) return item
        for (const child of item.children ?? []) {
            const found = findCapture(child)
            if (found) return found
        }
        return null
    }
    function checkSampling(surface) {
        const capture = findCapture(surface)
        if (!capture) return root.fail("Glass capture was not created")
        const rect = surface.mapToItem(null, Qt.rect(0, 0, surface.width, surface.height))
        const expected = Qt.rect(surface.winX + rect.x, surface.winY + rect.y, rect.width, rect.height)
        const actual = capture.sourceRect
        for (const key of ["x", "y", "width", "height"]) {
            if (Math.abs(actual[key] - expected[key]) > 2)
                return root.fail("Glass samples the final popup area instead of its visible area: " + key + "=" + actual[key] + ", expected " + expected[key] + ", step=" + root.step + ", tracking=" + surface.tracking + ", window=" + surface.Window.window + ", scene=" + surface.sceneRect)
        }
    }
    function checkIntensity(surface, expected = Config.options.background.widgets.glass.haze) {
        const capture = findCapture(surface)
        const effect = capture?.parent.children.find(item => item.fragmentShader !== undefined)
        if (!effect || effect.opacity !== 1 || Math.abs(effect.haze - expected) > 0.001)
            return root.fail("Glass intensity must increase blur without fading the surface")
    }
    function checkStreams(item) {
        if (item.captureSource !== undefined && item.hasContent !== undefined && item.captureSource !== null) {
            if (item.client.pid === Quickshell.processId) return root.fail("Glass captures its own window")
            if (!item.hasContent) return root.fail("Window backdrop has no captured frame")
        }
        for (const child of item.children ?? []) root.checkStreams(child)
    }
    Window {
        visible: false
        width: 160; height: 120
        WindowGlass { anchors.fill: parent; fullscreenSurface: true }
    }
    PanelWindow {
        id: host
        visible: true
        anchors.bottom: true
        anchors.right: true
        exclusiveZone: 0
        implicitWidth: 160
        implicitHeight: 36
        WlrLayershell.namespace: "quickshell:bar"
        WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
        color: "transparent"
        Item {
            x: 8; y: 6; width: 120; height: 24
            transform: [
                Scale { id: probeScale; origin.x: 60; origin.y: 12 },
                Translate { id: probeShift }
            ]
            WindowGlass { id: probe; anchors.fill: parent; cardRadius: 8 }
        }
        Item {
            id: target
            anchors.fill: parent
            property bool containsMouse: false
            MediaPopup {
                id: popup
                hoverTarget: target
                popupEnabled: true
                shouldShow: root.shown
            }
            ResourcesPopup {
                id: resourcesPopup
                hoverTarget: target
                shouldShow: root.shown
            }
            StyledPopup {
                id: intensityPopup
                hoverTarget: target
                shouldShow: root.shown
                popupColor: "#80304050"
                Text { text: "Glass"; color: "white" }
            }
        }
    }
    Timer {
        interval: 400
        running: Config.ready
        repeat: true
        onTriggered: {
            Config.options.background.widgets.glass.enhanced = root.step >= 10
            if (root.step === 0) {
                if (popup.active) return root.fail("Popup was allocated before its first opening")
            } else if (root.step % 2 === 1) {
                if (!popup.item || !popup.item.visible) return root.fail("Popup did not open")
                if (!root.firstWindow) {
                    root.firstWindow = popup.item
                    root.firstParent = popup.contentItem.parent
                }
                if ((popup.item !== root.firstWindow || popup.contentItem.parent !== root.firstParent))
                    return root.fail("Popup content moved to another native window")
                const glass = []
                root.collectGlass(popup.item.contentItem, glass)
                const enabled = Config.options.background.widgets.glass.enable
                const card = popup.contentItem.cardItem
                const surface = glass.find(item => item.parent === card)
                if (!surface || surface.live !== enabled || surface.cardRadius !== card.radius || card.radius <= 0)
                    return root.fail("Player glass does not follow the rounded card")
                if (enabled) {
                    root.checkSampling(surface)
                    root.checkStreams(surface)
                    root.checkIntensity(surface)
                }
                if (!resourcesPopup.item?.visible) return root.fail("Resources popup did not open")
                const resourceGlass = []
                root.collectGlass(resourcesPopup.item.contentItem, resourceGlass)
                const opaqueCards = resourceGlass.filter(item => item.parent?.frosted === true)
                if (opaqueCards.length !== 4) return root.fail("Resources popup must have four opaque cards")
                for (const card of opaqueCards) {
                    if (card.live !== enabled || (card.parent.color.a === 0) !== enabled)
                        return root.fail("Resource card does not follow glass mode")
                    if (enabled) {
                        root.checkSampling(card)
                        root.checkIntensity(card, Math.max(8, Config.options.background.widgets.glass.haze))
                    }
                }
                const popupGlass = []
                root.collectGlass(intensityPopup.item.contentItem, popupGlass)
                const popupSurface = popupGlass.find(item => item.parent?.margin !== undefined)
                const alpha = intensityPopup.popupColor.a
                if (!popupSurface || !popupSurface.glassEnabled || Math.abs(popupSurface.parent.color.a - alpha) > 0.005)
                    return root.fail("Glass intensity must preserve the popup background")
                if (enabled) root.checkIntensity(popupSurface)
                if (intensityPopup.contentItem.opacity !== 1)
                    return root.fail("Glass intensity fades the popup text")
                const outer = glass.find(item => item.parent?.margin !== undefined)
                if (!outer || outer.live)
                    return root.fail("An outer glass surface surrounds the player")
                if ((card.color.a === 0) !== enabled)
                    return root.fail("Player background does not follow glass mode")
                const artwork = card.children.find(item => item.sourceSize !== undefined)
                if (!artwork || artwork.visible === enabled)
                    return root.fail("Blurred album background overlaps the glass surface")
            } else {
                if (!popup.item || popup.item !== root.firstWindow || popup.item.visible)
                    return root.fail("Closing must hide the retained popup window")
                if (popup.contentItem.parent !== root.firstParent)
                    return root.fail("Closing detached the reusable popup content")
            }
            // Change transforms after the former one-second tracking timeout has expired.
            if ([4, 8, 16, 20].includes(root.step)) root.checkSampling(probe)
            if (root.step === 2) Config.options.background.widgets.glass.source = "windows"
            if (root.step === 4) Config.options.background.widgets.glass.haze = 8.5
            if (root.step === 8) Config.options.background.widgets.glass.haze = 16
            if (root.step === 16) Config.options.background.widgets.glass.haze = 12.25
            if (root.step === 18) Config.options.background.widgets.glass.haze = 1
            if ([5, 9, 17].includes(root.step)) root.checkStreams(probe)
            if ([1, 12, 19].includes(root.step) && GlassLayers.backdropConsumers !== 0)
                return root.fail("Window backdrop tracking remains active without consumers")
            if (root.step === 18) Config.options.background.widgets.glass.source = "wallpaper"
            if (root.step === 3) {
                probeScale.xScale = 0.35; probeScale.yScale = 0.6
                probeShift.x = 7; probeShift.y = 2
            }
            if (root.step === 7) {
                probeScale.xScale = 1.15; probeScale.yScale = 0.82
                probeShift.x = 11; probeShift.y = -3
            }
            if (root.step === 15) {
                probeScale.xScale = 0.9; probeScale.yScale = 0.3
                probeShift.x = -4; probeShift.y = 5
            }
            if (root.step === 19) {
                probeScale.xScale = 1; probeScale.yScale = 1
                probeShift.x = 0; probeShift.y = 0
            }
            if (root.step === 10) Config.options.background.widgets.glass.enable = false
            if (root.step === 14) Config.options.background.widgets.glass.enable = true
            root.step++
            if (root.step > 20) {
                console.log("Popup window lifecycle check passed")
                Qt.quit()
            } else root.shown = !root.shown
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
                            env=env, capture_output=True, text=True, timeout=25)
    output = result.stdout + result.stderr
    assert result.returncode == 0 and 'Popup window lifecycle check passed' in output, output
    assert not any(error in output for error in ('Cannot use same item on different windows', 'Failed to load configuration', 'Error:', 'TypeError:')), output
    print('Repeated native popup openings with glass and live texture passed')
