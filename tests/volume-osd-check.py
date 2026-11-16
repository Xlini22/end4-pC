"""Run: python3 tests/volume-osd-check.py (software rendering, no audio changes).
Exercise production volume/mute handlers, timeout and fullscreen routing.
"""
import os
from pathlib import Path
import re
import subprocess
import tempfile

repo = Path(__file__).resolve().parents[1]
source = (repo / 'modules/ii/onScreenDisplay/OnScreenDisplay.qml').read_text()
glass_source = (repo / 'modules/common/widgets/WindowGlass.qml').read_text()
glass_profile = re.search(r'readonly property string profileKey: ([^\n]+)', glass_source)[1]
glass_clear = re.search(r'readonly property bool clearMaterial: ([^\n]*(?:\n +&&[^\n]*)*)', glass_source)[1]
island_source = (repo / 'modules/ii/bar/DynamicIsland.qml').read_text()
island_osd = re.search(r'readonly property bool showOsd: ([^\n]*(?:\n +&&[^\n]*)*)', island_source)[1]
bar_source = (repo / 'modules/ii/bar/Bar.qml').read_text()
bar_covered = re.search(r'readonly property bool fullscreenCoversBar: ([^\n]*(?:\n +\?[^\n]*)*)', bar_source)[1].replace('WM.', 'fakeWM.')
bar_height = re.search(r'readonly property real visibleTopHeight: ([^\n]*(?:\n +(?:\|\||:)[^\n]*)*)', bar_source)[1]
# Keep production handlers/loaders; replace only external inputs and keep surfaces hidden.
source = source[:source.index('    IpcHandler {')] + "}\n"
source = source.replace('Scope {', 'ShellRoot {', 1)
source = source.replace('Audio.', 'fakeAudio.').replace('WM.', 'fakeWM.')
source = source.replace('target: Audio', 'target: fakeAudio')
source = source.replace('target: Brightness', 'target: fakeBrightness').replace('target: Hyprsunset', 'target: fakeGamma')
assert source.count('sourceComponent: FullscreenVolume { screen: root.volumePillScreen }') == 1
source = source.replace('sourceComponent: FullscreenVolume { screen: root.volumePillScreen }',
                        'sourceComponent: FullscreenVolume { screen: root.volumePillScreen; visible: false }')
source = source.replace('visible: osdLoader.active && !GlobalStates.dynamicIslandEnabled', 'visible: false')
source = source.replace('import qs\n', 'import qs\nimport qs.modules.ii.onScreenDisplay\n', 1)
check = r'''
    // Hidden surfaces have no QsWindow attachment: evaluate the production routing on their metadata.
    function profileForSurface(win, fullscreenSurface = false, floating = false, popup = false) {
        return GlassProfiles.profile(GLASS_PROFILE)
    }
    function clearSurface(win, floating = false, popup = false) { return GLASS_CLEAR }
    function barShowsOsd() { return ISLAND_OSD }
    QtObject { id: barContent; property real y: 0; property real height: 45 }
    QtObject { id: hoverRegion; property real y: 5 }
    QtObject {
        id: barRoot
        property var screen: Quickshell.screens[0]
        property var margins: ({top: 0})
        property bool monitorHasFullscreen: false
        property bool monitorHasSpecialOpen: false
        readonly property var compositorBarVisible: GlassCompositor.barVisibility[barRoot.screen?.name ?? ""]
        readonly property bool fullscreenCoversBar: BAR_COVERED
        readonly property real visibleTopHeight: BAR_HEIGHT
    }
    QtObject { id: fakeSink; property real volume: 0.5; property bool muted: false }
    QtObject {
        id: fakeAudio
        property bool ready: false
        property var sink: ({audio: fakeSink})
        signal sinkProtectionTriggered(string reason)
    }
    QtObject { id: fakeBrightness; signal brightnessChanged() }
    QtObject { id: fakeGamma; signal gammaChangeAttempt() }
    QtObject {
        id: fakeWM
        property var focusedMonitor: ({name: Quickshell.screens[0].name})
        property bool fullscreen: false
        function fullscreenOnMonitor(name) { return fullscreen && name === focusedMonitor.name }
    }
    Timer {
        id: check
        property int stage: 0
        interval: 150
        running: true
        function ensure(value, message) { if (!value) { console.error(message); Qt.quit(); throw new Error(message) } }
        onTriggered: {
            if (stage === 0) {
                ensure(Config.options.osd.timeout === 2500, "Volume must remain visible for 2.5 seconds")
                GlobalStates.startupLockPending = false
                GlobalStates.screenLocked = false
                Config.options.bar.bottom = false
                GlobalFocusGrab.barWindows = [barRoot]
                Config.options.bar.layouts.middleLayout = ["dynamicIsland"]
                GlobalStates.osdVolumeOpen = false
                fakeSink.volume = 0.6
                ensure(!GlobalStates.osdVolumeOpen, "Unready audio must not trigger an OSD")
                fakeAudio.ready = true
                fakeSink.volume = 0.7
                ensure(GlobalStates.osdVolumeOpen && osdTimeout.running, "Volume change must show and time the widget")
                ensure(!fullscreenVolumeLoader.active && !osdLoader.active, "Normal island must not create another OSD window")
                ensure(barShowsOsd(), "Ordinary volume changes must still appear in the bar")
                interval = 1500
            } else if (stage === 1) {
                ensure(GlobalStates.osdVolumeOpen, "Volume disappeared after the old one-second timeout")
                fakeSink.muted = true
                ensure(root.currentIndicator === "volume" && osdTimeout.running, "Mute must restart the same volume OSD")
                interval = 1700
            } else if (stage === 2) {
                ensure(GlobalStates.osdVolumeOpen, "Mute did not renew the duration from the last change")
                fakeWM.fullscreen = true
                ensure(root.fullscreenVolume && fullscreenVolumeLoader.active && !osdLoader.active,
                       "Fullscreen must route only to the compact overlay")
                ensure(!barShowsOsd(), "The bar must not duplicate volume while the pill is open")
                interval = 100
            } else if (stage === 3) {
                const notch = fullscreenVolumeLoader.item
                ensure(notch && !notch.visible && notch.screen === root.focusedScreen, "Notch must follow the focused monitor")
                ensure(notch.implicitWidth === 180 && notch.implicitHeight === 44, "Notch must contain the volume widget with room around its contents")
                const pill = notch.contentItem.children.find(item => item.iconForProviderId !== undefined)
                const content = pill?.children.find(item => item.di === pill)
                const glass = pill?.children.find(item => item.nativeRegion !== undefined)
                ensure(notch.WlrLayershell.namespace === "quickshell:bar" && GlassProfiles.keyFor(notch.WlrLayershell.namespace) === "bar"
                       && clearSurface(notch) && profileForSurface(notch) === GlassProfiles.profile("bar"),
                       "Fullscreen volume must inherit the actual bar profile in both native and fallback glass")
                const barProfile = profileForSurface(notch)
                barProfile.rim = 28
                barProfile.refraction = 190
                barProfile.blur = 2
                barProfile.reflections = 65
                ensure(profileForSurface(notch).rim === 28 && profileForSurface(notch).refraction === 190
                       && profileForSurface(notch).blur === 2 && profileForSurface(notch).reflections === 65,
                       "All four bar sliders must update the fullscreen pill's shared profile")
                ensure(content && content.x >= 10 && content.y >= 6
                       && content.x + content.width <= pill.width - 10
                       && content.y + content.height <= pill.height - 6,
                       "Volume contents must leave an inset on every side of the pill")
                Config.options.background.widgets.glass.elements.bar.enable = true
                Config.options.background.widgets.glass.enable = true
                ensure(glass?.live && pill.color.a === 0, "Active Glassy must not be covered by an opaque fill")
                Config.options.background.widgets.glass.enable = false
                ensure(!glass.live && Qt.colorEqual(pill.color, Appearance.colors.colLayer0), "Disabling Glassy must restore the normal fill")
                Config.options.background.widgets.glass.enable = true
                Config.options.background.widgets.glass.elements.bar.enable = false
                ensure(!glass.live && Qt.colorEqual(pill.color, Appearance.colors.colLayer0), "The bar Glassy toggle must also control the fullscreen pill")
                Config.options.background.widgets.glass.elements.bar.enable = true
                ensure(notch.exclusiveZone === 0 && notch.WlrLayershell.layer === WlrLayer.Overlay,
                       "Volume must overlay fullscreen without reserving desktop space")
                ensure(notch.WlrLayershell.keyboardFocus === WlrKeyboardFocus.None, "Volume must not steal keyboard focus")
                ensure(notch.margins.top === 5, "A fullscreen-covered bar must not displace the pill")
                const eventPrefix = String(Quickshell.processId) + "," + root.volumePillScreen.name
                GlassCompositor.receiveBarVisibility(eventPrefix + ",1,1")
                ensure(fakeWM.fullscreen && notch.margins.top === 55 && !barShowsOsd(),
                       "A gesture revealing the bar must push the pill before the active workspace changes")
                GlassCompositor.receiveBarSnapshot(JSON.stringify({serial: 0, bars: {}}))
                ensure(notch.margins.top === 55, "A stale initial reply must not undo a newer gesture event")
                GlassCompositor.receiveBarVisibility(eventPrefix + ",0,2")
                ensure(fakeWM.fullscreen && notch.margins.top === 5,
                       "Cancelling the gesture must restore the pill even though the workspace never changed")
                GlassCompositor.barVisibility = ({})
                fakeWM.fullscreen = false
                barRoot.monitorHasFullscreen = true // The polled workspace data can lag behind the native fullscreen state.
                ensure(root.detachedVolume && fullscreenVolumeLoader.active && !barShowsOsd(),
                       "Changing workspace must keep the existing burst solely in the pill")
                ensure(notch.margins.top === 5 + barRoot.visibleTopHeight && notch.margins.top === 55,
                       "A revealed top bar must push the pill below its bottom edge")
                barContent.y = -barContent.height
                ensure(notch.margins.top === 5, "An auto-hidden bar must release the pill's top position")
                barContent.y = -barContent.height / 2
                ensure(notch.margins.top > 5 && notch.margins.top < 55, "The pill must follow the bar during its reveal animation")
                barContent.y = 0
                barRoot.screen = {name: "another-monitor"}
                ensure(notch.margins.top === 5, "A bar on another monitor must not move the pill")
                barRoot.screen = Quickshell.screens[0]
                Config.options.bar.bottom = true
                ensure(notch.margins.top === 5, "A bottom bar cannot overlap a top pill")
                Config.options.bar.bottom = false
                fakeWM.fullscreen = true
                barRoot.monitorHasSpecialOpen = true
                ensure(notch.margins.top === 55, "A special workspace revealing the bar must push the pill down")
                barRoot.monitorHasSpecialOpen = false
                ensure(notch.margins.top === 5, "Returning to fullscreen must let the pill return to the top")
                root.currentIndicator = "brightness"
                ensure(!fullscreenVolumeLoader.active && barShowsOsd(), "Unrelated indicators must stay available in the bar")
                root.currentIndicator = "volume"
                GlobalStates.screenLocked = true
                ensure(!fullscreenVolumeLoader.active, "Notch must stay below the lock screen")
                GlobalStates.screenLocked = false
                GlobalStates.startupLockPending = true
                ensure(!fullscreenVolumeLoader.active, "Startup lock must suppress the notch")
                GlobalStates.startupLockPending = false
                fakeWM.fullscreen = false
                ensure(fullscreenVolumeLoader.active && !barShowsOsd(), "Leaving fullscreen must not duplicate or dismiss an active pill")
                interval = 1000
            } else {
                ensure(!GlobalStates.osdVolumeOpen && !fullscreenVolumeLoader.active, "OSD must close after inactivity")
                ensure(GlobalStates.osdVolumePillScreen === "", "Closing the pill must release its ownership")
                fakeSink.muted = false
                ensure(barShowsOsd() && !fullscreenVolumeLoader.active, "A fresh normal-desktop volume event must return to the bar")
                GlobalStates.osdVolumeOpen = false
                GlobalFocusGrab.barWindows = []
                console.log("VOLUME OSD CHECK PASSED")
                Qt.quit()
            }
            stage++
            if (stage < 5) restart()
        }
    }
'''
check = check.replace('GLASS_PROFILE', glass_profile).replace('GLASS_CLEAR', glass_clear).replace('ISLAND_OSD', island_osd).replace('BAR_HEIGHT', bar_height).replace('BAR_COVERED', bar_covered)
source = source.replace('    id: root\n', '    id: root\n' + check, 1)
display = os.environ.get('WAYLAND_DISPLAY', 'wayland-1')
if not display.startswith('/'):
    display = str(Path(os.environ.get('XDG_RUNTIME_DIR', f'/run/user/{os.getuid()}')) / display)
with tempfile.TemporaryDirectory(prefix='volume-osd-check-') as directory:
    temporary = Path(directory)
    shell = temporary / 'shell'
    shell.mkdir()
    for name in ('assets', 'defaults', 'modules', 'panelFamilies', 'scripts', 'services', 'translations'):
        (shell / name).symlink_to(repo / name, target_is_directory=True)
    for component in repo.glob('*.qml'):
        if component.name != 'shell.qml': (shell / component.name).symlink_to(component)
    harness = shell / 'shell.qml'
    harness.write_text(source)
    env = {**os.environ, 'QT_QPA_PLATFORM': 'wayland', 'WAYLAND_DISPLAY': display,
           'QT_QUICK_BACKEND': 'software', 'QT_QUICK_CONTROLS_STYLE': 'Basic',
           'QT_QPA_PLATFORMTHEME': '', 'QS_DISABLE_COMPOSITOR_GLASS': '1'}
    for kind in ('CONFIG', 'STATE', 'CACHE', 'DATA', 'RUNTIME'):
        folder = temporary / kind.lower()
        folder.mkdir(mode=0o700)
        env['XDG_' + kind + ('_HOME' if kind != 'RUNTIME' else '_DIR')] = str(folder)
    try:
        result = subprocess.run(['qs', '--no-color', '-p', str(harness)], cwd=repo,
                                env=env, text=True, capture_output=True, timeout=20)
    except subprocess.TimeoutExpired as error:
        raise AssertionError((error.stdout or b'').decode() + (error.stderr or b'').decode()) from error
    output = result.stdout + result.stderr
    assert result.returncode == 0 and 'VOLUME OSD CHECK PASSED' in output, output
    assert not re.search(r'(ReferenceError|TypeError|Binding loop|Unable to assign|Failed to load)', output), output
print('Volume/mute 2.5s timeout, renewal, workspace retention, bar displacement/no duplicates, monitor, lock and focus checks passed without audio changes.')
