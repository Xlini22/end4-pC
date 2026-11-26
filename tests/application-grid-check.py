"""Run python3 tests/application-grid-check.py; --render also exercises GPU rendering."""
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

repo = Path(__file__).resolve().parents[1]
render = '--render' in sys.argv
qml = '''//@ pragma UseQApplication
//@ pragma Env QT_QUICK_CONTROLS_STYLE=Basic
import QtQuick
import Quickshell
import qs.modules.common
import qs.services
ShellRoot {
    id: root
    property int step: 0
    property int launched: -1
    property int expected: 0
    property double lastFrame: 0
    property var frameIntervals: []
    property double deadline: Date.now() + 25000
    FrameAnimation {
        running: grid.testSlide.running
        onRunningChanged: root.lastFrame = 0
        onTriggered: {
            const now = Date.now()
            if (root.lastFrame) root.frameIntervals.push(now - root.lastFrame)
            root.lastFrame = now
        }
    }
    FloatingWindow {
        visible: true
        title: "Overview paging check"
        implicitWidth: grid.implicitWidth
        implicitHeight: grid.implicitHeight
        TestGrid {
            id: grid
            anchors.fill: parent
            applications: Array.from({length: 239}, (_, i) => ({
                name: "Application " + i,
                icon: i === 238 ? Quickshell.shellPath("assets/icons/flatpak-symbolic.svg")
                    : ["ark", "org.kde.dolphin", "firefox", "brave-desktop", "steam_icon_211820",
                        "F15B_ISIDE.0", "F99C_ISetup.0", "2E0E_ISetup-dark.0", "", "nonexistent-icon-xyz"][i % 10],
                runInTerminal: false, execute: () => { root.launched = i }
            }))
        }
    }
    function check(condition, message) {
        if (!condition) { console.error(message); Qt.quit(); throw new Error(message) }
    }
    function checkIcons(item) {
        if (item.entry !== undefined && item.visible) {
            const icon = item.contentItem.children.find(child => child.status !== undefined)
            root.check(icon?.asynchronous && icon.cache && icon.sourceSize.width > 0 && icon.sourceSize.height > 0,
                "Reused icons must use asynchronous, cached, size-limited decoding")
            if (icon.status === Image.Loading) return false
            root.check(icon.status === Image.Ready, "Application icon failed: " + item.entry.icon)
            const path = String(icon.source)
            root.check(path.startsWith("file:") || path.startsWith("/"),
                "Themed icons must resolve to real files, not placeholder providers: " + path)
            if (item.entry.icon === "steam_icon_211820" || item.entry.icon.endsWith(".0"))
                root.check(path.endsWith(item.entry.icon + ".png"), "Steam/Wine icon replaced by fallback: " + path)
            if (!item.entry.icon || item.entry.icon === "nonexistent-icon-xyz")
                root.check(path.includes("application-x-executable"), "Missing icon has no generic fallback")
        }
        for (const child of item.children ?? []) if (!checkIcons(child)) return false
        return true
    }
    Timer {
        interval: 60; repeat: true; running: Config.ready
        onTriggered: {
            root.check(Date.now() < root.deadline, "Paging check timed out at step " + root.step + " (animation=" + grid.testSlide.running + ")")
            const view = grid.testView
            view.forceLayout()
            for (const button of grid.testIndicators.children.filter(item => item.selected !== undefined)) {
                const dot = button.contentItem.children[0]
                root.check(dot.width === dot.height && dot.radius === dot.width / 2,
                    "Page indicators must stay circular during layout and animation")
            }
            if (grid.testSlide.running) return
            if (root.step > 0 && !root.checkIcons(view.currentItem)) return
            root.check(view.currentIndex === root.expected, "Wrong selected page")
            if (root.step > 0)
                root.check(Math.abs(view.contentX - root.expected * view.width) < 1,
                    "Animation did not settle on the selected page")
            if (root.step === 0) {
                const icons = SystemAppearance.resolvedIcons[SystemAppearance.iconTheme] ?? {}
                if (["ark", "org.kde.dolphin", "firefox", "brave-desktop", "steam_icon_211820",
                    "F15B_ISIDE.0", "F99C_ISetup.0", "2E0E_ISetup-dark.0", "application-x-executable"].some(name => !icons[name])) return
                grid.testSlide.duration = 80
                root.check(grid.pageCount === 18, "Last partial page is missing")
                for (const delta of [-20, 20]) {
                    grid.swipeCoolingDown = false
                    const event = {pixelDelta:{x:delta}, angleDelta:{x:0}, accepted:false}
                    grid.handlePageWheel(event)
                    root.check(event.accepted && view.currentIndex === (delta < 0 ? 1 : 0),
                        "Two-finger scrolling must move the page with the gesture")
                }
            }
            if (root.step < 60) {
                // ponytail: cover both directions, distant pages and interrupted animations without real pointer input.
                const next = root.step < 36 ? root.step % 18
                    : root.step % 3 === 0 ? 17 : root.step % 3 === 1 ? 0 : 8
                grid.showPage((next + 1) % 18)
                grid.showPage(next)
                root.expected = next
                root.step++
            } else if (root.step === 60) {
                console.log("PAGING COUNTERS " + JSON.stringify({pages:grid.pagesCreated,
                    buttons:grid.buttonsCreated, livePages:grid.pagesCreated-grid.pagesDestroyed,
                    width:view.width, contentWidth:view.contentWidth, cache:view.cacheBuffer}))
                const frames = root.frameIntervals.sort((a, b) => a - b)
                console.log("PAGING FRAMES " + JSON.stringify({count:frames.length,
                    p95:frames[Math.floor(frames.length * .95)], max:frames[frames.length-1]}))
                root.check(grid.pagesCreated - grid.pagesDestroyed <= 8, "Live pages keep accumulating")
                root.check(grid.pagesCreated <= 12, "Page objects keep being rebuilt: " + grid.pagesCreated)
                root.check(grid.buttonsCreated <= 12 * 14, "Application buttons keep being rebuilt: " + grid.buttonsCreated)
                grid.showPage(17)
                root.expected = 17
                root.step++
            } else if (root.step === 61) {
                const page = view.currentItem
                const buttons = []
                function collect(item) {
                    if (item.entry !== undefined) buttons.push(item)
                    for (const child of item.children ?? []) collect(child)
                }
                collect(page)
                const shown = buttons.filter(button => button.visible)
                root.check(shown.length === 1 && shown[0].entry.name === "Application 238",
                    "A reused partial page shows stale applications")
                root.checkIcons(page)
                shown[0].clicked()
                root.check(root.launched === 238, "A reused button launches the wrong application")
                grid.showPage(999)
                root.check(view.currentIndex === 17, "Page upper bound is not clamped")
                grid.showPage(-1)
                root.expected = 0
                root.step++
            } else {
                root.check(view.currentIndex === 0, "Page lower bound is not clamped")
                console.log("APPLICATION GRID CHECK PASSED")
                Qt.quit()
            }
        }
    }
}
'''
display = os.environ.get('WAYLAND_DISPLAY', 'wayland-1')
if not display.startswith('/'):
    display = str(Path(os.environ.get('XDG_RUNTIME_DIR', f'/run/user/{os.getuid()}')) / display)
with tempfile.TemporaryDirectory(prefix='ag-') as directory:
    temporary = Path(directory)
    env = {**os.environ, 'QT_QPA_PLATFORM': 'wayland', 'WAYLAND_DISPLAY': display,
           'QT_QUICK_BACKEND': '' if render else 'software', 'QT_QPA_PLATFORMTHEME': '',
           'QS_DISABLE_COMPOSITOR_GLASS': '1'}
    for kind in ('CONFIG', 'STATE', 'CACHE', 'DATA', 'RUNTIME'):
        path = temporary / ('r' if kind == 'RUNTIME' else kind.lower())
        path.mkdir(mode=0o700)
        env['XDG_' + kind + '_HOME' if kind != 'RUNTIME' else 'XDG_RUNTIME_DIR'] = str(path)
    # Resolve named icons using the real desktop theme, while keeping all writes temporary.
    config_home = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))
    if (config_home / 'kdeglobals').exists():
        shutil.copyfile(config_home / 'kdeglobals', temporary / 'config/kdeglobals')
    env['XDG_DATA_DIRS'] = os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local/share')) + ':' + os.environ.get('XDG_DATA_DIRS', '/usr/local/share:/usr/share')
    (temporary / 'r/hypr').symlink_to(Path(os.environ['XDG_RUNTIME_DIR']) / 'hypr', target_is_directory=True)
    shell = temporary / 'shell'
    shell.mkdir()
    for name in ('assets', 'defaults', 'modules', 'panelFamilies', 'scripts', 'services', 'translations'):
        (shell / name).symlink_to(repo / name, target_is_directory=True)
    for component in repo.glob('*.qml'):
        if component.name != 'shell.qml':
            (shell / component.name).symlink_to(component)
    # Test counters and synthetic entries stay outside the watched desktop configuration.
    source = (repo / 'modules/ii/overview/ApplicationGrid.qml').read_text()
    start = source.index('    readonly property var applications:')
    end = source.index('    readonly property int pageCount:', start)
    source = source[:start] + '    property var applications: []\n' + source[end:]
    source = source.replace('id: root', '''id: root
    property alias testView: appPages
    property alias testIndicators: pageIndicators
    property alias testSlide: pageSlideAnimation
    property int pagesCreated: 0
    property int pagesDestroyed: 0
    property int buttonsCreated: 0''', 1)
    source = source.replace('id: appPage\n', '''id: appPage
                Component.onCompleted: root.pagesCreated++
                Component.onDestruction: root.pagesDestroyed++\n''', 1)
    source = source.replace('id: appButton', '''id: appButton
                            Component.onCompleted: root.buttonsCreated++''', 1)
    (shell / 'TestGrid.qml').write_text(source)
    (shell / 'shell.qml').write_text(qml)
    try:
        result = subprocess.run(['qs', '--no-color', '-p', str(shell)], env=env, cwd=repo,
                                capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired as error:
        raise AssertionError((error.stdout or b'').decode() + (error.stderr or b'').decode()) from error
    output = '\n'.join(dict.fromkeys((result.stdout + result.stderr).splitlines()))
    assert result.returncode == 0 and 'APPLICATION GRID CHECK PASSED' in output, output
    assert not re.search(r'(ReferenceError|TypeError|Binding loop|Unable to assign|Failed to load)', output), output
    print(next(line for line in output.splitlines() if 'PAGING COUNTERS' in line))
    print(next(line for line in output.splitlines() if 'PAGING FRAMES' in line))
    print('60 page switches, bounded objects, partial-page content and launch, interruptions and bounds passed')
