"""Run python3 tests/sidebar-window-check.py in Wayland; uses isolated preferences."""
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
import qs.modules.ii.sidebarLeft as Left
ShellRoot {
    id: root
    property var cachedContent: null
    property int phase: 0
    property int cycle: 0
    property bool checkedWidth: false
    property double due: 0
    property double deadline: Date.now() + 45000
    Left.SidebarLeft { id: sidebar }
    function fail(message) { console.error(message); Qt.quit() }
    Connections {
        target: sidebar.sidebarContent?.Window.window ?? null
        function onFrameSwapped() {
            const background = sidebar.sidebarContent?.parent
            if (background && background.Window.window.width < background.x + background.width - 1)
                root.fail("Sidebar surface clips its width animation")
            const win = sidebar.sidebarContent?.QsWindow.window
            if (root.phase === 4 && WM.compositor === "hyprland"
                && win.implicitWidth > Appearance.sizes.sidebarWidth + Appearance.sizes.elevationMargin + 1)
                root.fail("Reopening temporarily widens the compact sidebar")
        }
    }
    function collect(item, result) {
        if (item.nativeRegion !== undefined && item.glassEnabled) result.push(item)
        for (const child of item.children ?? []) collect(child, result)
    }
    Timer {
        interval: 100; repeat: true; running: Config.ready
        onTriggered: {
            if (Date.now() > root.deadline) return root.fail("Sidebar lifecycle timed out: " + root.phase)
            if (Date.now() < root.due) return
            if (root.phase === 0) {
                if (sidebar.loaded || sidebar.sidebarContent) return root.fail("Sidebar allocated before opening")
                Config.options.background.widgets.glass.enable = true
                Config.options.background.widgets.glass.enhanced = true
                Config.options.sidebar.mainPage = "home"
                Config.options.sidebar.leftRememberPage = false
                Config.options.policies.ai = 1
                Config.options.policies.weeb = 1
                Config.options.sidebar.media.enable = true
                Config.options.sidebar.translator.enable = true
                Config.options.sidebar.football.enable = true
                GlobalStates.sidebarLeftOpen = true
                root.phase = 1
            } else if (root.phase === 1) {
                if (!sidebar.sidebarContent) return
                root.cachedContent = sidebar.sidebarContent
                root.due = Date.now() + 1800
                root.phase = 2
            } else if (root.phase === 2) {
                if (!sidebar.loaded || sidebar.sidebarContent !== root.cachedContent)
                    return root.fail("Sidebar content was recreated")
                if (!root.checkedWidth && WM.compositor === "hyprland") {
                    const win = sidebar.sidebarContent.QsWindow.window
                    if (win.width > Appearance.sizes.sidebarWidth + Appearance.sizes.elevationMargin + 1)
                        return root.fail("Compact sidebar keeps an unused wide surface")
                    win.extend = true
                    root.phase = 6
                    root.due = Date.now() + 700
                    return
                }
                GlobalStates.sidebarLeftOpen = false
                root.due = Date.now() + 3400
                root.phase = 3
            } else if (root.phase === 3) {
                if (!sidebar.loaded || sidebar.sidebarContent !== root.cachedContent)
                    return root.fail("Glassy sidebar was evicted while hidden")
                let item = sidebar.sidebarContent
                while (item.parent) item = item.parent
                const glass = []
                root.collect(item, glass)
                if (glass.length < 7) return root.fail("Home cards did not load")
                if (glass.some(surface => surface.tracking) || GlassLayers.backdropConsumers !== 0)
                    return root.fail("Hidden sidebar keeps rendering glass")
                GlobalStates.sidebarLeftOpen = true
                root.due = Date.now() + 500
                root.phase = 4
            } else if (root.phase === 4) {
                if (sidebar.sidebarContent !== root.cachedContent)
                    return root.fail("Reopening lost the cached sidebar")
                root.cycle++
                if (root.cycle < 3) root.phase = 2
                else {
                    Config.options.background.widgets.glass.enable = false
                    GlobalStates.sidebarLeftOpen = false
                    root.due = Date.now() + 3400
                    root.phase = 5
                }
            } else if (root.phase === 6) {
                const win = sidebar.sidebarContent.QsWindow.window
                if (win.width < Appearance.sizes.sidebarWidthExtended)
                    return root.fail("Extended sidebar did not grow its surface")
                win.extend = false
                root.phase = 7
                root.due = Date.now() + 700
            } else if (root.phase === 7) {
                const win = sidebar.sidebarContent.QsWindow.window
                if (win.width > Appearance.sizes.sidebarWidth + Appearance.sizes.elevationMargin + 1)
                    return root.fail("Collapsed sidebar did not release unused surface width")
                root.checkedWidth = true
                root.phase = 2
            } else {
                if (sidebar.loaded || sidebar.sidebarContent) return root.fail("Standard sidebar no longer releases its content")
                console.log("Sidebar window lifecycle passed")
                Qt.quit()
            }
        }
    }
}
'''

# ponytail: share the existing isolated Wayland runner instead of duplicating its profile setup.
runner = (repo / 'tests/settings-window-check.py').read_text().split("display = os.environ.get", 1)[1]
runner = 'display = os.environ.get' + runner
runner = runner.replace('Settings window lifecycle', 'Sidebar window lifecycle')
runner = runner.replace('Real settings: lazy pages, repeated open/close and all glass modes passed',
                        'Glassy sidebar reuses content across three delayed reopenings, stops hidden glass and preserves normal cleanup')
exec(compile(runner, str(repo / 'tests/settings-window-check.py'), 'exec'))
