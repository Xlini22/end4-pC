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
import qs.modules.ii.background as Background
import qs.modules.ii.settings as Settings
import qs.modules.ii.settings.pages as Pages
import qs.modules.ii.sidebarLeft as Left
import qs.modules.ii.sidebarRight as Right
import qs.modules.ii.overview as Overview
import qs.modules.ii.lock as Lock
import qs.modules.common.widgets as Widgets
ShellRoot {
    id: root
    Lock.Lock {}
    property bool contrastActive: true
    property var contrastSamples: []
    property int contrastTick: 0
    property real dashboardScrollEnd: -1
    property Item glassKnob: null
    property Item volumeSlider: null
    Widgets.RippleButton {
        id: hoverCheck
        width: 200; height: 40
        colBackground: Qt.rgba(.2,.4,.6,0)
    }
    Widgets.ConfigSwitch { id: switchHoverCheck }
    QtObject {
        id: contrastCacheProbe
        property bool contrastActive: true
        property bool uniformDarkeningAvailable: true
        property int contrastTick: 0
        property string regionsApplied: "initial"
        property var calls: ({count: 0})
        property var glassItems: [{nativeRegion: () => { contrastCacheProbe.calls.count++; return {} }}]
        CONTRAST_MATERIAL_CACHE
    }
    function checkContrastCache() {
        const settings = Config.options.background.widgets.glass.elements.settings
        const saved = settings.automaticDarkening
        settings.automaticDarkening = true
        let snapshot = contrastCacheProbe.contrastMaterialSnapshot
        const before = contrastCacheProbe.calls.count
        for (let i = 0; i < 30; ++i) {
            contrastCacheProbe.regionsApplied = String(i)
            snapshot = contrastCacheProbe.contrastMaterialSnapshot
        }
        if (contrastCacheProbe.calls.count !== before)
            throw new Error("Scrolling geometry must not rebuild the text contrast cache every frame")
        contrastCacheProbe.contrastTick++
        snapshot = contrastCacheProbe.contrastMaterialSnapshot
        if (contrastCacheProbe.calls.count !== before + 1 || snapshot.regions.length !== 1)
            throw new Error("A fresh brightness sample must refresh the text contrast geometry")
        settings.automaticDarkening = saved
        console.log("CONTRAST MATERIAL CACHE PASSED")
    }
    function checkTransparentHover() {
        if (switchHoverCheck.colBackground.a !== 0 || !Qt.colorEqual(switchHoverCheck.colBackground, switchHoverCheck.colBackgroundHover))
            throw new Error("Switch rows must keep identical transparent idle/hover colours")
        hoverCheck.colBackground = Qt.rgba(.7,.3,.2,0)
        if (!Qt.colorEqual(hoverCheck.background.color, hoverCheck.buttonColor))
            throw new Error("Fully transparent hover must not animate invisible RGB")
        hoverCheck.colBackground = Qt.rgba(.4,.7,.2,1)
        if (hoverCheck.background.color.a >= 1)
            throw new Error("Visible hover fade-in must retain its animation")
    }
    function checkHoverFade() {
        if (hoverCheck.background.color.a !== 1)
            throw new Error("Visible hover fade-in did not finish")
        hoverCheck.colBackground = Qt.rgba(.3,.5,.8,1)
        if (Qt.colorEqual(hoverCheck.background.color, hoverCheck.buttonColor))
            throw new Error("Visible color changes must retain their animation")
        hoverCheck.colBackground = Qt.rgba(.3,.5,.8,0)
        if (hoverCheck.background.color.a <= 0)
            throw new Error("Visible hover fade-out must retain its animation")
        console.log("TRANSPARENT HOVER CHECK PASSED")
    }
    property int previousCalls: 0
    property int nextCalls: 0
    QtObject {
        id: testPlayer
        property real volume: 0.42
        property bool isPlaying: false
        property bool canSeek: false
        property int playbackState: 0
        property string trackTitle: "Test track"
        property string trackArtist: "Test artist"
        property string trackArtUrl: ""
        function previous() { root.previousCalls++ }
        function next() { root.nextCalls++ }
    }
    PanelWindow {
        visible: false
        implicitWidth: 450; implicitHeight: 900
        Left.SidebarPlayerControl {
            id: mediaControls
            anchors.fill: parent
            radius: 20
            player: testPlayer
        }
    }
    PanelWindow {
        visible: false
        implicitWidth: 450; implicitHeight: 1100
        Right.SidebarRightContent { id: rightSidebar; width: 450; height: 1100 }
    }
    PanelWindow {
        visible: false
        implicitWidth: 780; implicitHeight: 680
        Pages.GlassyConfig { id: glassySettings; anchors.fill: parent }
        Widgets.WindowGlass { id: lockedGlass; fullscreenSurface: true; width: 100; height: 40 }
    }
    FloatingWindow {
        visible: false
        title: "illogical-impulse Settings"
        Widgets.DashboardCard { id: floatingCard; width: 180; height: 90; tint: "#4080a0" }
    }
    function checkGlassy() {
        Config.options.background.widgets.glass.enable = true
        if (GlassProfiles.keys.join(",") !== "bar,dock,sidebar,settings,lockscreen,terminal") throw new Error("Missing Glassy tabs")
        for (let i=0; i<GlassProfiles.keys.length; ++i) {
            const key = GlassProfiles.keys[i]
            glassySettings.selectedTab = i
            if (glassySettings.profile !== GlassProfiles.profile(key)) throw new Error("Wrong profile after tab navigation")
            const expected = GlassProfiles.defaults(key)
            for (const field of Object.keys(expected)) if (glassySettings.profile[field] !== expected[field]) throw new Error("Unexpected default: " + key + ":" + field)
        }
        for (let i=0; i<GlassProfiles.keys.length; ++i) {
            glassySettings.selectedTab = i
            const p = glassySettings.profile
            p.enable = true
            const slider = findControl(glassySettings, item => item.objectName === "glass-darkening")
            const automatic = findControl(glassySettings, item => item.objectName === "glass-automatic-darkening")
            if (!slider || !automatic || !slider.enabled) throw new Error("Missing darkening controls")
            slider.value = 37 + i
            slider.moved()
            if (p.darkening !== 37 + i) throw new Error("Manual darkening not saved")
            automatic.checked = true
            if (!p.automaticDarkening || slider.enabled || p.darkening !== 37 + i) throw new Error("Automatic must disable slider and retain value")
            automatic.checked = false
            if (!slider.enabled || p.darkening !== 37 + i) throw new Error("Manual darkening not restored")
        }
        for (let i=0; i<GlassProfiles.keys.length; ++i) {
            if (GlassProfiles.profile(GlassProfiles.keys[i]).darkening !== 37+i) throw new Error("Darkening leaked between targets")
            GlassProfiles.reset(GlassProfiles.keys[i])
        }
        Config.options.background.widgets.glass.elements.lockscreen.enable = false
        if (lockedGlass.live) throw new Error("Lockscreen Glassy toggle ignored")
        Config.options.background.widgets.glass.elements.lockscreen.enable = true
        if (!lockedGlass.live) throw new Error("Lockscreen Glassy toggle did not restore material")
        const namespaces = ["quickshell:bar", "quickshell:dock", "quickshell:sidebarLeft", "quickshell:settings"]
        for (const namespace of namespaces) {
            const key = GlassProfiles.keyFor(namespace), p = GlassProfiles.profile(key)
            p.enable=false
            if (GlassProfiles.enabledFor(namespace)) throw new Error("Target toggle ignored: " + key)
            p.enable=true
        }
        if (!GlassProfiles.enabledFor("quickshell:popup")) throw new Error("Unrelated popup changed")
        glassySettings.selectedTab = 0
        root.glassKnob = findControl(glassySettings, item => item.objectName === "glass-refraction")
        if (!root.glassKnob) throw new Error("Glassy controls did not instantiate")
        root.glassKnob.value = 175
        GlobalStates.settingsSubpage = "glassy"
        findControl(glassySettings, item => item.objectName === "glassy-back").clicked()
        if (GlobalStates.settingsSubpage !== "") throw new Error("Back navigation did not return to settings")
    }
    function findControl(item, predicate) {
        if (predicate(item)) return item
        for (const child of item.children ?? []) {
            const found = findControl(child, predicate)
            if (found) return found
        }
        return null
    }
    function checkRightSidebar() {
        const saved = Config.options.background.widgets.glass.enable
        const background = rightSidebar.children.find(item => item.border !== undefined)
        const outer = background.children.find(item => item.nativeRegion !== undefined)
        function collect(item, result) {
            if (item.nativeRegion !== undefined && item.frost >= 8) result.push(item)
            for (const child of item.children ?? []) collect(child, result)
        }
        for (const banner of [true, false]) for (const style of ["android", "classic"]) {
            Config.options.sidebar.banner = banner
            Config.options.sidebar.quickToggles.style = style
            Config.options.background.widgets.glass.enable = true
            const blocks = []
            collect(rightSidebar, blocks)
            if (blocks.length !== 8 || !outer.live || outer.frost !== 0
                    || background.color.a !== 0 || background.border.width !== 0)
                throw new Error("Right sidebar must have one clear shell, five frosted sections and three frosted notification controls: " + banner + ":" + style + ":" + blocks.length)
            for (const glass of blocks) {
                const button = glass.parent.parent
                const fill = button.glassFrost !== undefined ? button.paintedColor : glass.parent.color
                if (!glass.live || (fill !== undefined && fill.a !== 0))
                    throw new Error("A solid section fill covers right sidebar glass")
            }
            Config.options.background.widgets.glass.enable = false
            if (outer.live || !Qt.colorEqual(background.color, Appearance.colors.colUiBackground)
                    || background.border.width !== 1 || blocks.some(glass => glass.live))
                throw new Error("Disabling Glassy must restore the original right sidebar")
            if (blocks.filter(glass => glass.parent.color !== undefined
                    && Qt.colorEqual(glass.parent.color, Appearance.colors.colLayer1)).length < (banner ? 4 : 3))
                throw new Error("Right sidebar sections lost their original solid backgrounds")
        }
        rightSidebar.showIconPickerDialog = true
        const dialog = findControl(rightSidebar, item => item.backgroundWidth !== undefined && item.glass !== undefined)
        const dialogGlass = dialog && findControl(dialog, item => item.nativeRegion !== undefined)
        const sections = findControl(rightSidebar, item => item.fillKey === "notifications")
        if (!dialog?.glass || !dialog.show || !dialogGlass || dialogGlass.frost < 8)
            throw new Error("Every right sidebar dialog must opt into the shared frosted container")
        if (dialogGlass.parent.radius !== Appearance.rounding.large
                || dialogGlass.cardRadius !== dialogGlass.parent.radius
                || dialogGlass.parent.children.some(item => item.radius !== undefined))
            throw new Error("Dialog glass must retain the original rounded container without inset rectangles")
        for (const enabled of [true, false, true]) {
            Config.options.background.widgets.glass.enable = true
            Config.options.background.widgets.glass.elements.sidebar.enable = enabled
            if (rightSidebar.activeDialog !== dialog || sections.layer.enabled !== enabled
                    || dialogGlass.live !== enabled || (enabled ? dialogGlass.parent.color.a !== 0
                    : !Qt.colorEqual(dialogGlass.parent.color, Appearance.m3colors.m3surfaceContainerHigh)))
                throw new Error("Sidebar dialog glass must follow the sidebar toggle and restore its solid fill")
        }
        Config.options.background.widgets.glass.enable = false
        if (dialogGlass.live || !Qt.colorEqual(dialogGlass.parent.color, Appearance.m3colors.m3surfaceContainerHigh))
            throw new Error("Disabling Glassy must restore the dialog's original background")
        if (sections.layer.enabled) throw new Error("A solid dialog must not allocate a backdrop mask")
        dialog.dismiss()
        if (rightSidebar.showIconPickerDialog || dialog.show)
            throw new Error("Glassy dialogs must retain their existing dismissal behavior")
        Config.options.background.widgets.glass.enable = saved
        console.log("RIGHT SIDEBAR GLASS PASSED")
    }
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
            checkHoverFade()
            checkRightSidebar()
            root.glassKnob.moved()
            if (Math.abs(GlassProfiles.profile("bar").refraction-175)>.01 || GlassProfiles.profile("dock").refraction!==135)
                throw new Error("Glassy controls must update only the selected element")
            GlassProfiles.reset("bar")
            if (GlassProfiles.profile("bar").refraction!==200) throw new Error("Glassy reset failed")
            console.log("GLASSY PAGE CONTROLS PASSED")
            const card = recycledCard.item
            if (card.animOpacity !== 0 || Math.abs(card.offsetX - card.travelX) > .001)
                throw new Error("Animated tiles must also leave when the page changes")
            if (!findControl(dashboardSettings, item => item.modelData?.kind === "card"
                    && item.active && item.status === Loader.Ready && item.item?.animScale !== undefined))
                throw new Error("Dashboard tiles must complete creation while the page is idle")
            root.volumeSlider.moved()
            if (Math.abs(testPlayer.volume - .73) > .001)
                throw new Error("Sidebar volume slider must control the selected player")
            console.log("SIDEBAR MEDIA CONTROLS PASSED")
            console.log("SYNC COMPONENT COMPILE PASSED")
            Qt.quit()
        }
    }
    Component { Families.IllogicalImpulseFamily {} }
    Component { Background.Background {} }
    Component { Pages.BarConfig {} }
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
            const previous = findControl(mediaControls, item => item.contentItem?.text === "skip_previous" && item.downAction !== undefined)
            const play = findControl(mediaControls, item => item.contentItem?.text === "play_arrow" && item.downAction !== undefined)
            const next = findControl(mediaControls, item => item.contentItem?.text === "skip_next" && item.downAction !== undefined)
            if (!previous || !play || !next || previous.parent !== play.parent || next.parent !== play.parent)
                throw new Error("Sidebar must group previous, play and next in the same row")
            previous.downAction()
            next.downAction()
            if (root.previousCalls !== 1 || root.nextCalls !== 1)
                throw new Error("Sidebar skip controls must target the selected player")
            root.volumeSlider = findControl(mediaControls, item => item.moved !== undefined && item.highlightColor !== undefined)
            if (!root.volumeSlider || Math.abs(root.volumeSlider.value - .42) > .001)
                throw new Error("Sidebar must show the selected player's volume")
            root.volumeSlider.value = .73
            checkTransparentHover()
            checkContrastCache()
            checkGlassy()
            Config.options.background.widgets.glass.enable = false
            if (dashboardCard.color.a !== 1) throw new Error("Standard Dashboard cards must retain their tint")
            Config.options.background.widgets.glass.enable = true
            const material = dashboardCard.children.find(item => item.nativeRegion !== undefined)
            GlassCompositor.windowFrostedAvailable = false
            if (material.live || dashboardCard.color.a !== 1)
                throw new Error("Unavailable Dashboard glass must use solid cards, without a wallpaper or screencopy fallback")
            GlassCompositor.windowFrostedAvailable = true
            if (!material || !material.live || material.frost < 8 || material.nativeClip !== cardViewport)
                throw new Error("Dashboard must use the shared clipped frosted material")
            if (Math.abs(dashboardCard.color.a - .72) > .01 || Math.abs(dashboardCard.color.r - 64/255) > .01)
                throw new Error("Frosted Dashboard must preserve card hue")
            const floatingMaterial = floatingCard.children.find(item => item.nativeRegion !== undefined)
            Config.options.background.widgets.glass.elements.settings.enable = false
            if (floatingMaterial.live || floatingCard.color.a !== 1)
                throw new Error("Disabling Settings glass must restore opaque Dashboard cards")
            Config.options.background.widgets.glass.elements.settings.enable = true
            if (!floatingMaterial.live)
                throw new Error("Dashboard must restore frosted cards when Settings glass is enabled")
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
            const initialPreload = view.preloadY
            for (let i = 1; i < 100; ++i) {
                view.contentY = initialPreload + i / 10
                if (view.preloadY !== initialPreload)
                    throw new Error("Small touchpad movements must not reevaluate every tile's preload range")
            }
            view.contentY = initialPreload + dashboardSettings.rowHeight
            if (view.preloadY !== initialPreload + dashboardSettings.rowHeight)
                throw new Error("Tile preload range must advance before the next row becomes visible")
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
    material_cache = re.search(r'    readonly property var contrastMaterialSnapshot: \{[\s\S]*?\n    \}', compositor)[0]
    harness.write_text(qml.replace('CONTRAST_MATERIAL_CACHE', material_cache)
                       .replace('CONTRAST_SOCKET', actual_socket)
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
    assert 'GLASSY PAGE CONTROLS PASSED' in output, output
    assert 'TRANSPARENT HOVER CHECK PASSED' in output, output
    assert 'CONTRAST MATERIAL CACHE PASSED' in output, output
    assert 'RIGHT SIDEBAR GLASS PASSED' in output, output
    assert not re.search(r'(ReferenceError|TypeError|Binding loop|Unable to assign)', output), output
    print('Panel family, direct scrolling and contrast IPC retention/error fallback passed without GPU rendering')
