"""Run python3 tests/sidebar-transition-check.py; exercises real sidebar pages in isolation."""
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
    property var slots: []
    readonly property var pageLayout: sidebar.sidebarContent?.children.find(item => item.spacing !== undefined) ?? null
    property int phase: 0
    property int step: 0
    property int frames: 0
    property int switches: 0
    property int tileMotionFrames: 0
    property string previousKey: "home"
    property var tiles: []
    property double due: 0
    property double deadline: Date.now() + 30000
    readonly property var destinations: ["ai", "media", "home", "ai", "home"]
    Left.SidebarLeft { id: sidebar }
    function fail(message) { console.error(message); Qt.quit() }
    function collect(item) {
        if (item.pageKey !== undefined && item.current !== undefined) root.slots.push(item)
        for (const child of item.children ?? []) collect(child)
    }
    function collectTiles(item) {
        if (item.animIndex !== undefined && item.offsetX !== undefined) root.tiles.push(item)
        for (const child of item.children ?? []) collectTiles(child)
    }
    Connections {
        target: sidebar.sidebarContent
        function onDisplayedKeyChanged() {
            if (!root.slots.length) return
            const layout = root.pageLayout
            if (layout.opacity > 0.001) root.fail("Page/layout changed before fade: " + layout.opacity + " key=" + sidebar.sidebarContent.displayedKey + " step=" + root.step)
            const slot = root.slots.find(item => item.pageKey === sidebar.sidebarContent.displayedKey)
            if (!slot?.ready) root.fail("Incoming page shown before its loader was ready")
            if (root.previousKey === "home" && sidebar.sidebarContent.displayedKey !== "home"
                && root.tiles.some(tile => tile.animOpacity > 0.001))
                root.fail("Home tiles hidden before their exit finished")
            root.previousKey = sidebar.sidebarContent.displayedKey
            root.switches++
        }
    }
    Connections {
        target: sidebar.sidebarContent?.Window.window ?? null
        function onFrameSwapped() {
            if (!root.slots.length) return
            const visible = root.slots.filter(slot => slot.visible)
            if (visible.length !== 1) return root.fail("Sidebar pages overlap or disappear")
            const slot = visible[0]
            if (slot.pageKey === "home" && !slot.item.active && root.pageLayout.opacity > 0.999
                && root.tiles.some(tile => tile.animOpacity > 0.05 && Math.abs(tile.offsetX) > 2))
                root.tileMotionFrames++
            const box = slot.parent.parent
            const glass = box.children.find(item => item.nativeRegion !== undefined)
            if (!glass || glass.glassEnabled !== (slot.pageKey !== "home"))
                return root.fail("Page and glass background switched at different times")
            if (["ai", "media"].includes(slot.pageKey) && glass.frost < 8)
                return root.fail("Incoming page lost its frosted material")
            if (glass.mapToItem(slot, 0, 0).x !== 0 || glass.mapToItem(slot, 0, 0).y !== 0)
                return root.fail("Glass background detached from page")
            root.frames++
        }
    }
    Timer {
        interval: 40; repeat: true; running: Config.ready
        onTriggered: {
            if (Date.now() > root.deadline) return root.fail("Sidebar transition timed out: " + root.phase)
            if (Date.now() < root.due) return
            const content = sidebar.sidebarContent
            if (root.phase === 0) {
                Config.options.background.widgets.glass.enable = true
                Config.options.policies.ai = 1
                Config.options.sidebar.media.enable = true
                Config.options.sidebar.mainPage = "home"
                Config.options.sidebar.leftRememberPage = false
                Config.options.settings.animationSpeed = 0.5
                GlobalStates.sidebarLeftOpen = true
                root.phase = 1
                root.due = Date.now() + 800
            } else if (root.phase === 1) {
                if (!content) return
                root.collect(content)
                root.collectTiles(root.slots.find(slot => slot.pageKey === "home").item)
                if (root.slots.length < 3) return root.fail("Sidebar slots did not load")
                content.goTo(root.destinations[0])
                root.phase = 2
                root.due = Date.now() + 900
            } else if (root.phase === 2) {
                if (content.displayedKey !== root.destinations[root.step]
                    || root.pageLayout.opacity < 0.999)
                    return
                root.step++
                if (root.step < root.destinations.length) {
                    content.goTo(root.destinations[root.step])
                    root.due = Date.now() + 900
                } else {
                    Config.options.settings.animationSpeed = 2
                    content.goTo("ai")
                    root.phase = 3
                    root.due = Date.now() + 40
                }
            } else if (root.phase === 3) {
                content.goTo("media")
                root.phase = 4
                root.due = Date.now() + 80
            } else if (root.phase === 4) {
                content.goTo("home")
                root.phase = 5
                root.due = Date.now() + 800
            } else {
                if (content.displayedKey !== "home" || root.pageLayout.opacity < 0.999)
                    return root.fail("Interrupted navigation did not return home")
                if (root.frames < 20 || root.switches < 5) return root.fail("Insufficient transition samples")
                if (root.tileMotionFrames < 3) return root.fail("Home tiles no longer animate visibly on selection")
                console.log("Sidebar transition passed", root.frames, "frames", root.switches, "page changes")
                Qt.quit()
            }
        }
    }
}
'''

# ponytail: reuse the isolated Wayland runner; keep test QML outside the watched desktop config.
runner = (repo / 'tests/settings-window-check.py').read_text().split("display = os.environ.get", 1)[1]
runner = 'display = os.environ.get' + runner
runner = runner.replace('Settings window lifecycle passed', 'Sidebar transition passed')
runner = runner.replace('Real settings: lazy pages, repeated open/close and all glass modes passed',
                        'Sidebar transitions: no overlapping pages, synchronized frosted box, async readiness and interrupted navigation passed')
exec(compile(runner, str(repo / 'tests/settings-window-check.py'), 'exec'))
