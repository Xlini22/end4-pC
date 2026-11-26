"""Run python3 tests/overview-performance-check.py in a Wayland session.
Exercise the production overview with temporary settings; brief test windows close automatically.
"""
import os
import json
from pathlib import Path
import re
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
import qs.modules.ii.settings.pages as Pages
ShellRoot {
    id: root
    property int phase: 0
    property int cycles: 0
    property var cached: null
    property double deadline: Date.now() + 15000
    TestOverview { id: overview }
    Connections {
        target: overview.testPanel
        function onVisibleChanged() {
            if (root.phase >= 2 && root.phase <= 4 && !overview.testPanel.visible)
                root.check(!overview.testPanel.overviewAnimating,
                    "Closing hid the window before its animations finished")
        }
    }
    PanelWindow {
        visible: false
        implicitWidth: 800; implicitHeight: 800
        Pages.GlassyConfig { id: settings; width: 800; height: 800 }
    }
    function materials(item, result) {
        if (item.nativeRegion !== undefined && item.frost === 8) result.push(item)
        for (const child of item.children ?? []) materials(child, result)
        return result
    }
    function checkGlass(enabled) {
        const items = materials(overview.testPanel.contentItem, [])
        check(items.length === 3, "Overview needs search, workspaces and applications materials: " + items.length)
        for (const glass of items) {
            check(glass.profileKey === "overview" && glass.live === enabled, "Overview profile/toggle not applied: " + glass.profileKey + " live=" + glass.live + " expected=" + enabled + " win=" + glass.win + " parent=" + glass.parent)
            check(glass.cardRadius === glass.parent.radius, "Glass lost its container radius")
            check(enabled ? glass.parent.color.a === 0 : glass.parent.color.a > 0, "Solid fallback obscures the glass")
            check(!glass.tracking, "Hidden overview must not track glass geometry or captures")
        }
    }
    function checkProfile() {
        const glass = Config.options.background.widgets.glass
        glass.enable = true
        const p = glass.elements.overview
        settings.selectedTab = GlassProfiles.keys.indexOf("overview")
        check(settings.profile === p && settings.tabs[settings.selectedTab].length > 0, "Missing Overview settings tab")
        const barRim = glass.elements.bar.rim
        settings.writeValue("rim", 19)
        settings.writeValue("blur", 12)
        settings.writeValue("automaticDarkening", true)
        check(p.rim === 19 && p.blur === 12 && p.automaticDarkening && glass.elements.bar.rim === barRim,
            "Editing Overview must not change another profile")
        settings.resetSelected()
        const defaults = GlassProfiles.defaults("overview")
        for (const field of Object.keys(defaults)) check(p[field] === defaults[field], "Overview reset failed: " + field)
        settings.writeValue("rim", 19)
        checkGlass(true)
        p.enable = false
        check(!GlassProfiles.enabledFor("quickshell:overview"), "Overview namespace ignores its toggle")
        checkGlass(false)
        p.enable = true
        glass.enable = false
        checkGlass(false)
        glass.enable = true
        checkGlass(true)
        check(GlassCompositor.nativeProfileKeys.length === 6, "Legacy HyprGlass must still receive six profiles")
        GlassCompositor.overviewProfilesAvailable = true
        check(GlassCompositor.nativeProfileKeys.length === 7, "Updated HyprGlass must receive the Overview profile")
        GlassCompositor.overviewProfilesAvailable = false
    }
    function check(condition, message) {
        if (!condition) { console.error(message); Qt.quit(); throw new Error(message) }
    }
    function checkCaptures(item, connected, live = connected) {
        if (item.captureSource !== undefined) {
            check(connected ? item.captureSource !== null : item.captureSource === null,
                "Capture source does not follow preview visibility: phase=" + root.phase + " connected=" + connected + " parentVisible=" + item.parent.visible + " open=" + GlobalStates.overviewOpen + " presented=" + overview.testPanel.presented + " preview=" + overview.preview)
            check(item.live === live, "Capture activity does not follow overview animation/visibility at phase " + root.phase)
        }
        for (const child of item.children ?? []) checkCaptures(child, connected, live)
    }
    function previews(item, result) {
        if (item.dragStartX !== undefined) result.push(item)
        for (const child of item.children ?? []) previews(child, result)
        return result
    }
    Timer {
        interval: 100; repeat: true; running: Config.ready
        onTriggered: {
            root.check(Date.now() < root.deadline, "Overview lifecycle timed out at phase " + root.phase)
            const loader = overview.testLoader
            if (root.phase === 0) {
                overview.testPanel.visible = true
                Config.options.overview.enable = true
                Config.options.overview.style = "default"
                root.phase = 1
            } else if (root.phase === 1) {
                if (loader.status !== Loader.Ready || !HyprlandData.monitors.length) return
                root.checkProfile()
                overview.testPanel.visible = Qt.binding(() => overview.testPanel.presented || overview.preview)
                root.cached = loader.item
                root.check(!GlobalStates.overviewOpen, "Overview should preload while closed")
                root.checkCaptures(loader.item, false)
                GlobalStates.overviewOpen = true
                root.phase = 2
            } else if (root.phase === 2) {
                root.check(loader.item === root.cached, "Opening rebuilt the workspace tree")
                if (overview.testPanel.overviewAnimating) {
                    root.checkCaptures(loader.item, true, false)
                    return
                }
                root.checkCaptures(loader.item, true)
                for (const window of root.previews(loader.item, [])) {
                    root.check(!window.dragging && !window.pressed && !window.Drag.active,
                        "Reopening retained a stale drag")
                    window.dragging = true
                    window.pressed = true
                    window.Drag.active = true
                    window.x = -100
                    window.y = -100
                }
                loader.item.draggingFromWorkspace = 1
                overview.testPanel.searchingText = "test"
                root.phase = 3
            } else if (root.phase === 3) {
                root.check(!loader.item.visible, "Searching must hide workspace previews")
                root.checkCaptures(loader.item, false)
                root.check(loader.item.draggingFromWorkspace === -1, "Hiding retained a drag source")
                for (const window of root.previews(loader.item, []))
                    root.check(!window.dragging && !window.pressed && !window.Drag.active,
                        "Hiding must cancel cached window interactions")
                overview.testPanel.searchingText = ""
                GlobalStates.overviewOpen = false
                root.phase = 4
            } else if (root.phase === 4) {
                if (overview.testPanel.presented) {
                    root.checkCaptures(loader.item, true, false)
                    return
                }
                root.check(loader.status === Loader.Ready && loader.item === root.cached,
                    "Closing destroyed the cached workspace tree")
                root.checkCaptures(loader.item, false)
                if (++root.cycles < 3) {
                    GlobalStates.overviewOpen = true
                    root.phase = 2
                } else {
                    Config.options.overview.style = "niri"
                    root.phase = 5
                }
            } else if (root.phase === 5) {
                if (loader.status !== Loader.Ready) return
                root.check(loader.item !== root.cached, "Changing style must replace the cached tree")
                root.checkCaptures(loader.item, false)
                Config.options.overview.enable = false
                root.phase = 6
            } else if (root.phase === 6) {
                root.check(!loader.active && loader.item === null, "Disabling overview must release its tree")
                Config.options.overview.style = "default"
                Config.options.overview.enable = true
                root.phase = 7
            } else if (root.phase === 7) {
                if (loader.status !== Loader.Ready) return
                root.checkCaptures(loader.item, false)
                for (const glass of root.materials(overview.testPanel.contentItem, []))
                    root.check(!glass.tracking, "Closed overview still tracks glass")
                GlobalStates.settingsOpen = true
                settings.preview = true
                root.check(overview.preview && !GlobalStates.overviewOpen, "Overview preview must preserve the open state")
                settings.preview = false
                GlobalStates.settingsOpen = false
                root.check(!overview.preview, "Overview preview did not clean up")
                console.log("OVERVIEW PERFORMANCE CHECK PASSED: preload, 3 reopen cycles, hidden captures, style and enable switches")
                Qt.quit()
            }
        }
    }
}
'''
display = os.environ.get('WAYLAND_DISPLAY', 'wayland-1')
if not display.startswith('/'):
    display = str(Path(os.environ.get('XDG_RUNTIME_DIR', f'/run/user/{os.getuid()}')) / display)
with tempfile.TemporaryDirectory(prefix='ov-') as directory:
    temporary = Path(directory)
    env = {**os.environ, 'QT_QPA_PLATFORM': 'wayland', 'WAYLAND_DISPLAY': display,
           'QT_QUICK_BACKEND': '', 'QT_QPA_PLATFORMTHEME': '', 'QS_DISABLE_COMPOSITOR_GLASS': '1'}
    for kind in ('CONFIG', 'STATE', 'CACHE', 'DATA', 'RUNTIME'):
        path = temporary / ('r' if kind == 'RUNTIME' else kind.lower())
        path.mkdir(mode=0o700)
        env['XDG_' + kind + '_HOME' if kind != 'RUNTIME' else 'XDG_RUNTIME_DIR'] = str(path)
    (temporary / 'r/hypr').symlink_to(
        Path(os.environ.get('XDG_RUNTIME_DIR', f'/run/user/{os.getuid()}')) / 'hypr', target_is_directory=True)
    shell = temporary / 'shell'
    shell.mkdir()
    for name in ('assets', 'defaults', 'modules', 'panelFamilies', 'scripts', 'services', 'translations'):
        (shell / name).symlink_to(repo / name, target_is_directory=True)
    for component in repo.glob('*.qml'):
        if component.name != 'shell.qml':
            (shell / component.name).symlink_to(component)
    # ponytail: expose test handles in a temporary copy, keeping the desktop untouched.
    overview = (repo / 'modules/ii/overview/Overview.qml').read_text()
    overview = overview.replace('import qs\n', 'import qs\nimport qs.modules.ii.overview\n', 1)
    overview = overview.replace('id: overviewScope', 'id: overviewScope\n    property alias testLoader: overviewLoader\n    property alias testPanel: panelWindow', 1)
    overview = overview.replace('visible: panelWindow.presented || overviewScope.preview', 'visible: false', 1)
    (shell / 'TestOverview.qml').write_text(overview)
    (shell / 'shell.qml').write_text(qml)
    try:
        result = subprocess.run(['qs', '--no-color', '-p', str(shell)], cwd=repo,
                                env=env, capture_output=True, text=True, timeout=25)
    except subprocess.TimeoutExpired as error:
        raise AssertionError((error.stdout or b'').decode() + (error.stderr or b'').decode()) from error
    output = result.stdout + result.stderr
    assert result.returncode == 0 and 'OVERVIEW PERFORMANCE CHECK PASSED' in output, output
    assert not re.search(r'(ReferenceError|TypeError|Binding loop|Unable to assign|Failed to load)', output), output
    saved = json.loads((temporary / 'config/illogical-impulse/config.json').read_text())
    assert saved['background']['widgets']['glass']['elements']['overview']['rim'] == 19
    print('Overview glass tab, independent edits/reset/persistence, toggles and hidden materials passed')
    print('Overview preload, cached reopen, hidden captures, style and enable switches passed')
