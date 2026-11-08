"""Run python3 tests/dock-magnify-check.py. Software rendering; no mapped windows or native glass."""
import os
from pathlib import Path
import subprocess
import tempfile

repo = Path(__file__).resolve().parents[1]
dock_source = (repo / 'modules/ii/dock/Dock.qml').read_text()
start = dock_source.index('                        Rectangle {\n                            id: dockVisualBackground')
background = dock_source[start:dock_source.index('\n                        RoundCorner {', start)]
qml = '''//@ pragma UseQApplication
//@ pragma Env QT_QUICK_CONTROLS_STYLE=Basic
import QtQuick
import Quickshell
import qs.modules.common
import qs.modules.common.widgets
import qs.modules.ii.dock as Dock
ShellRoot {
    id: root
    property bool passed: false
    function check(value, message) { if (!value) throw new Error(message) }
    PanelWindow {
        id: window
        visible: false
        implicitWidth: 300; implicitHeight: 100
        Dock.DockPinButton { id: pin; x: 10; y: 30; width: 35; height: 35 }
        DockSeparator { id: first; x: 55; y: 25; width: 1; height: 40 }
        DockButton {
            id: app; x: 70; y: 15; width: 50; height: 50; magnifiable: true
            innerInset: DockStyle.iconInset; outerInset: DockStyle.iconInset
            magnifyBaseline: contentItem.y + contentItem.iconBottom
            contentItem: DockAppIcon { iconSource: Qt.resolvedUrl("assets/icons/github-symbolic.svg"); anchors.centerIn: parent }
        }
        DockAppButton {
            id: inlineSeparator
            x: 130; y: 15; width: 1; height: 50
            appToplevel: ({appId: "SEPARATOR", toplevels: []})
        }
        DockSeparator { id: last; x: 150; y: 25; width: 1; height: 40 }
        Dock.DockAppsButton { id: apps; x: 175; y: 15; width: 50; height: 50 }
        DockAppButton {
            id: running; x: 240; y: 15; width: 50; height: 50
            iconSize: 29
            appToplevel: ({appId: "image-missing", toplevels: []})
        }
        Item {
            id: dockRoot
            width: 260; height: 80
            property bool hug: Config.options.dock.style === "hug"
            property bool vertical: DockStyle.vertical
            property bool macos: DockStyle.magnifying
            property real hugFlare: 0
            property real gap: 0
            property real shadowMargin: 0
            property string position: DockStyle.position
            property color backgroundColor: "#203040"
            property real borderWidth: Config.options.dock.showBackground && Config.options.dock.showBorder ? 1 : 0
            DOCK_BACKGROUND
        }
    }
    Timer {
        interval: 200; running: true
        onTriggered: {
            try {
                Config.options.dock.showPinButton = true
                Config.options.dock.showAppsButton = true
                Config.options.dock.magnify = true
                Config.options.dock.magnification = 1.6
                DockStyle.position = "bottom"
                window.contentItem.visible = true // Exercise geometry without showing the native window.
                Config.options.dock.showBackground = true
                Config.options.dock.showBorder = true
                Config.options.background.widgets.glass.enable = false
                root.check(dockVisualBackground.color.a === 1 && dockVisualBackground.border.width === 1, "Standard dock must retain its background and border")
                const glass = dockVisualBackground.children.find(item => item.nativeRegion !== undefined)
                Config.options.background.widgets.glass.enable = true
                root.check(glass.live && glass.frost >= 8 && dockVisualBackground.color.a === 0 && dockVisualBackground.border.width === 0,
                    "Glassy dock must use one frosted surface, without an opaque fill or outline over it")
                Config.options.dock.style = "hug"
                root.check(glass.bottomLeftRadius === 0 && glass.bottomRightRadius === 0, "Frosted geometry must retain the dock's attached corners")
                Config.options.dock.showBackground = false
                root.check(!glass.live && dockVisualBackground.color.a === 0 && dockVisualBackground.border.width === 0, "Hidden background must not leave a glass surface")
                const items = [pin, first, app, last, apps, running]
                const iconBottom = button => {
                    const icon = button === running ? button.contentItem.item : button.contentItem
                    const image = icon.children[0]
                    return image.mapToItem(null, image.width / 2, image.height).y
                }
                const pinSymbol = pin.children[0].children[0].contentItem
                root.check(pinSymbol.renderType === Text.QtRendering && apps.contentItem.renderType === Text.QtRendering,
                    "Pin and launcher glyphs must use scalable text rendering")
                const icons = [app.contentItem, running.contentItem.item]
                const images = icons.map(icon => icon.children[0].item.backer)
                const symbolBottom = symbol => symbol.mapToItem(null, symbol.width / 2, (symbol.height + symbol.iconSize) / 2).y
                const baselines = [app, running].map(iconBottom)
                const symbolBaselines = [pinSymbol, apps.contentItem].map(symbolBottom)
                root.check(items.every(item => item.magnifyId >= 0), "All dock controls must register for magnification")
                root.check(inlineSeparator.magnifyId === -1, "Inline separator's outer button must not register twice")
                const inner = DockMagnify.entries.find(entry => !items.includes(entry.item))?.item
                root.check(!!inner && inner.parent.parent === inlineSeparator, "Inline separator must register its actual line")
                root.check(DockMagnify.entries.length === 7, "Unexpected or duplicate magnification registrations")
                // A hidden PanelWindow has no backing QWindow: supply only that association, retaining real item geometry.
                DockMagnify.entries = DockMagnify.entries.map(entry => ({id:entry.id,item:{
                    QsWindow:{window:window}, get visible() {return entry.item.visible},
                    get parent() {return entry.item.parent}, get x() {return entry.item.x},
                    get width() {return entry.item.width}}}))
                DockMagnify.window = window
                DockMagnify.amplitude = 1
                for (const magnification of [1.2, 1.6, 2.2]) {
                  Config.options.dock.magnification = magnification
                  const requestedSizes = icons.map(icon => Math.ceil(icon.iconSize * magnification))
                  for (const [index, image] of images.entries())
                      root.check(image.sourceSize.width === requestedSizes[index] && image.sourceSize.height === requestedSizes[index],
                          "SVG and theme icons must load at the maximum zoom resolution")
                  root.check(images[0].status === Image.Ready && images[0].implicitWidth >= requestedSizes[0],
                      "SVG must actually be rasterized at the requested resolution")
                  let reloads = 0
                  const countReload = () => { reloads++ }
                  for (const image of images) image.sourceSizeChanged.connect(countReload)
                  for (const pointer of [27.5, 55.5, 95, 130.5, 150.5, 200, 265]) {
                    DockMagnify.pointer = pointer
                    root.check(Object.keys(DockMagnify.values).length === 7, "Magnification must include pin, lines, apps and launcher: " + JSON.stringify(DockMagnify.entries.map(entry => ({visible:entry.item.visible,sameWindow:entry.item.QsWindow.window === window}))))
                    for (const [index, button] of [app, running].entries())
                        root.check(Math.abs(iconBottom(button) - baselines[index]) < .01,
                            "Magnification must keep the pinned/running icon's lower edge fixed: " + iconBottom(button) + " vs " + baselines[index])
                    for (const [index, symbol] of [pinSymbol, apps.contentItem].entries())
                        root.check(Math.abs(symbolBottom(symbol) - symbolBaselines[index]) < .01,
                            "Pin and launcher symbols must keep their lower edge fixed")
                    const ordered = [pin, first, app, inner, last, apps, running].map(item => {
                        const base = item.parent.mapToItem(null, item.x + item.width / 2, 0).x
                        const value = DockMagnify.values[item.magnifyId]
                        root.check(item.scale >= 1 && item.scale <= magnification, "Dock item must enlarge within the configured limit")
                        const painted = item.mapToItem(null, item.width / 2, item.height).x
                        root.check(Math.abs(painted - base - value.shift) < .01, "Dock controls must follow their computed horizontal shift")
                        return painted
                    })
                    for (let i = 1; i < ordered.length; i++)
                        root.check(ordered[i] > ordered[i-1], "Magnified controls must retain their order")
                  }
                  for (const image of images) image.sourceSizeChanged.disconnect(countReload)
                  root.check(reloads === 0, "Hovering must reuse the loaded texture without changing its resolution")
                }
                Config.options.dock.showPinButton = false
                DockMagnify.recompute()
                root.check(!DockMagnify.values[pin.magnifyId], "Hidden pin must leave the magnification wave")
                DockStyle.position = "left"
                DockMagnify.recompute()
                root.check(DockMagnify.totalExtra === 0 && items.every(item => item.scale === 1), "Vertical dock must retain its original geometry")
                root.check(images.every((image, index) => image.sourceSize.width === Math.ceil(icons[index].iconSize)),
                    "Vertical dock must load only its normal icon resolution")
                DockStyle.position = "bottom"
                Config.options.dock.magnify = false
                DockMagnify.recompute()
                root.check(items.every(item => item.scale === 1), "Disabling magnification must restore original sizes")
                root.check(images.every((image, index) => image.sourceSize.width === Math.ceil(icons[index].iconSize)),
                    "Disabling magnification must restore normal icon resolution")
                // A regular row matching the reference: 40px icons with 12px gaps.
                Config.options.dock.iconSize = 40
                Config.options.dock.magnification = 2.2
                Config.options.dock.magnify = true
                const entries = DockMagnify.entries
                DockMagnify.entries = [0, 52, 104, 156, 208].map((center, id) => ({id:1000 + id,item:{
                    QsWindow:{window:window}, visible:true, parent:window.contentItem, x:center - 20, width:40}}))
                const rowOrigin = window.contentItem.mapToItem(null, 0, 0).x
                for (const offset of [-110.001, -110, -55, 0, 55, 110, 110.001]) {
                    DockMagnify.pointer = rowOrigin + 104 + offset
                    const value = DockMagnify.values[1002]
                    const expectedScale = 1 + 1.2 * Math.max(0, 1 - Math.abs(offset) / 110)
                    const expectedShift = Math.abs(offset) > 110 ? -Math.sign(offset) * 38.4 : -offset / 110 * 38.4 * expectedScale
                    root.check(Math.abs(value.scale - expectedScale) < .00001 && Math.abs(value.shift - expectedShift) < .00001,
                        "Icon spacing must follow the reference's distance/nudge curve at centers and influence boundaries")
                    const row = [1000,1001,1002,1003,1004].map((id, index) => {
                        const item = DockMagnify.values[id]
                        return {center:index*52 + item.shift, radius:20*item.scale}
                    })
                    for (let i = 1; i < row.length; i++)
                        root.check(row[i].center - row[i].radius >= row[i-1].center + row[i-1].radius,
                            "Reference spacing must keep neighboring app images apart")
                }
                DockMagnify.amplitude = 0
                root.check(DockMagnify.totalExtra === 0 && Object.keys(DockMagnify.values).length === 0,
                    "Leaving the dock must restore zero spacing and background expansion")
                DockMagnify.entries = entries
                Config.options.dock.iconSize = 33
                // Exercise a visible-window association while keeping the native test window hidden.
                DockMagnify.window = ({visible:true})
                Config.options.dock.showPinButton = true
                const baseline = iconBottom(app)
                const controls = [...items, inner]
                for (const [scale, shift] of [[2,32], [1.4,-16], [1,0]]) {
                    const values = {}
                    for (const item of controls) values[item.magnifyId] = {scale:scale,shift:shift}
                    DockMagnify.values = values
                    DockMagnify.leftExtra = Math.abs(shift)
                    DockMagnify.rightExtra = Math.abs(shift) / 2
                    root.check(controls.every(item => item.scale === scale && item.transform[0].x === shift),
                        "Dock controls must follow the latest scale and position directly, without spring motion")
                    root.check(Math.abs(iconBottom(app) - baseline) < .01,
                        "The icon's lower edge must remain fixed while reversing direction")
                    root.check(dockVisualBackground.anchors.leftMargin === -DockMagnify.leftExtra
                        && dockVisualBackground.anchors.rightMargin === -DockMagnify.rightExtra,
                        "Dock background must follow its expansion directly, without spring motion")
                }
                console.log("DOCK MAGNIFICATION PASSED")
                root.passed = true
            } catch (error) { console.error(error.message) }
            Qt.quit()
        }
    }
}
'''.replace('DOCK_BACKGROUND', background)
with tempfile.TemporaryDirectory(prefix='dock-check-', dir='/tmp') as directory:
    base = Path(directory)
    display = os.environ.get('WAYLAND_DISPLAY', 'wayland-1')
    if not display.startswith('/'):
        display = str(Path(os.environ.get('XDG_RUNTIME_DIR', '/run/user/' + str(os.getuid()))) / display)
    env = {**os.environ, 'QT_QPA_PLATFORM': 'wayland', 'WAYLAND_DISPLAY': display, 'QT_QUICK_BACKEND': 'software',
           'QT_QPA_PLATFORMTHEME': '', 'QS_DISABLE_COMPOSITOR_GLASS': '1'}
    for kind in ('CONFIG', 'STATE', 'CACHE', 'DATA', 'RUNTIME'):
        target = base / kind.lower()
        target.mkdir(mode=0o700)
        env['XDG_' + kind + ('_DIR' if kind == 'RUNTIME' else '_HOME')] = str(target)
    shell = base / 'shell'
    shell.mkdir()
    for name in ('assets', 'defaults', 'modules', 'panelFamilies', 'scripts', 'services', 'translations'):
        (shell / name).symlink_to(repo / name, target_is_directory=True)
    for file in repo.glob('*.qml'):
        if file.name != 'shell.qml': (shell / file.name).symlink_to(file)
    harness = shell / 'shell.qml'
    harness.write_text(qml)
    result = subprocess.run(['qs', '--no-color', '-p', str(harness)], env=env, text=True,
                            capture_output=True, timeout=20)
    output = result.stdout + result.stderr
    assert result.returncode == 0 and 'DOCK MAGNIFICATION PASSED' in output, output
    print('Dock: reference spacing/boundaries, direct tracking without spring motion, high-resolution icons without hover reloads, fixed baselines, hidden/vertical/off controls and frosted background states passed.')
