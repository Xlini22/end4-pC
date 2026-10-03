"""Run with python3 tests/media-popup-check.py (Qt 6 QtTest required)."""
import os
import re
from pathlib import Path
import subprocess
import tempfile

repo = Path(__file__).resolve().parents[1]
popup = (repo / 'modules/common/widgets/StyledPopup.qml').read_text()
player = (repo / 'modules/common/widgets/Player.qml').read_text()
media_popup = (repo / 'modules/ii/bar/MediaPopup.qml').read_text()
controls = (repo / 'modules/common/widgets/PlayerControls.qml').read_text()
di_media = (repo / 'modules/ii/bar/DiMedia.qml').read_text()
island = (repo / 'modules/ii/bar/DynamicIsland.qml').read_text()
media_hover = island[island.index('            HoverHandler {\n                id: mediaSideHover'):island.index('            Component.onDestruction:', island.index('id: mediaSideHover'))]
title_text = re.search(r'id: trackTitle\b[\s\S]*?text: ([^\n]+)', controls)[1]
artist_text = re.search(r'id: trackArtist\b[\s\S]*?text: ([^\n]+)', controls)[1]
play_action = next(line.split('downAction: ', 1)[1] for line in controls.splitlines() if 'downAction:' in line and 'togglePlaying()' in line)
popup_enabled = re.search(r'    popupEnabled: ([\s\S]*?)\n    property bool barHovered:', media_popup)[1]
media_enabled = re.search(r'enabled: (contentAvailable[^\n]+)', island)[1]
bridge = media_popup[media_popup.index('    onTargetHoveredChanged:'):media_popup.index('    Player {')].replace('root.', 'bridge.')
bar_click = di_media[di_media.index('        MouseArea {'):di_media.index('        layer.enabled:')]
bar_controls = di_media[di_media.index('        RowLayout {\n            id: mediaControlsRow'):di_media.rindex('\n    }\n}')]
# Use production hover placement and artwork bindings, with native interactive controls.
hover = popup[popup.index('        Item {\n            id: inputArea'):popup.index('            anchors {', popup.index('            id: body'))]
hover = hover.replace('            id: body', '            id: body; x: 20; y: 20; width: 300; height: 180')
art_override = next(line for line in player.splitlines() if ' artSourceOverride:' in line)
color = player[player.index('    property color artDominantColor:'):player.index('    property bool downloaded:')]
art_path = player[player.index('    property string displayedArtFilePath:'):player.index('    property QtObject blendedColors:')]
art_changed = player[player.index('    onArtFilePathChanged:'):player.index('    Process {')]
qml = '''import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtTest
Item {
    id: root
    width: 400; height: 250
    property bool popupHovered: false
    property bool mediaControlsOpen: false
    property bool useSharedTimeline: true
    property var player: null
    property string rememberedTitle: TITLE_TEXT
    property string rememberedArtist: ARTIST_TEXT
    property var playAction: PLAY_ACTION
    QtObject { id: stringUtils; function cleanMusicTitle(text) { return text } }
    QtObject { id: popupGate
        property var activePlayer: null
        property bool popupEnabled: POPUP_ENABLED
    }
    property var artUrl: "file:///old-track.png"
    property string artFilePath: "old-track.png"
    property bool downloaded: true
    property bool hasMedia: true
    property bool componentInteractionReady: false
    property bool mediaHovered: false
    property bool isMaterial: false
    property var activePlayer: fakePlayer
    QtObject { id: fakePlayer
        property bool canGoPrevious: true
        property bool canGoNext: true
        property bool isPlaying: true
        property int previousCalls: 0
        property int nextCalls: 0
        function previous() { previousCalls++ }
        function next() { nextCalls++ }
    }
    QtObject { id: controller
        property string displayTrackTitle: "Kado"
        property string displayTrackArtist: "Yung Bae"
        property bool hasRememberedTrack: false
        property int raiseCalls: 0
        property int toggleCalls: 0
        function raiseActivePlayer() { raiseCalls++ }
        function togglePlaying() { toggleCalls++ }
    }
    QtObject { id: config
        property var options: ({bar: {dynamicIsland: {showMediaControls: true}}})
    }
    component MaterialSymbol: Text { property real fill; property real iconSize }
    Item {
        id: bar
        x: 20; y: 210; width: 300; height: 32
        property bool contentAvailable: true
        property string modelData: "media"
        enabled: MEDIA_ENABLED
        MEDIA_HOVER
        BAR_CLICK
        Rectangle { x: 0; width: 32; height: 32; color: "blue" }
        Text { x: 40; text: "Track title" }
        Item { x: 170; width: 40; height: 32 }
        BAR_CONTROLS
    }
    QtObject {
        id: bridge
        property bool targetHovered: false
        property bool popupHovered: false
        property bool barHovered: false
        property bool hoverBridgeActive: false
        property bool shouldShow: targetHovered || popupHovered || hoverBridgeActive
        property int closeCalls: 0
        onShouldShowChanged: if (!shouldShow) closeCalls++
        BRIDGE
    }
    OVERRIDE
    COLOR
    ART_PATH
    ART_CHANGED
    QtObject { id: Appearance
        property var colors: ({colPrimary: "blue", colPrimaryContainer: "white", colOnLayer0: "white"})
        property var m3colors: ({m3secondaryContainer: "gray"})
    }
    QtObject { id: ColorUtils; function mix(a, b, factor) { return a } }
    QtObject { id: colorQuantizer; property var colors: ["red"] }
    QtObject { id: coverArtDownloader
        property string targetFile; property string artFilePath; property bool running: false
    }
    HOVER
            Button { id: play; x: 80; y: 30; text: "Play"; hoverEnabled: true }
            Slider { id: progress; x: 30; y: 110; width: 240; hoverEnabled: true }
        }
    Image { id: cover; source: root.displayedArtFilePath }
    TestCase {
        name: "MediaPopup"
        when: windowShown
        function test_remembered_track_controls() {
            compare(root.rememberedTitle, "Kado")
            compare(root.rememberedArtist, "Yung Bae")
            const calls = controller.toggleCalls
            root.playAction()
            compare(controller.toggleCalls, calls + 1)
            root.useSharedTimeline = false
            compare(root.rememberedTitle, "Untitled")
            compare(root.rememberedArtist, "")
            root.playAction()
            compare(controller.toggleCalls, calls + 1)
            root.useSharedTimeline = true
            controller.toggleCalls = 0
        }
        function test_popup_with_remembered_track() {
            controller.hasRememberedTrack = false
            compare(popupGate.popupEnabled, false)
            controller.hasRememberedTrack = true
            compare(popupGate.popupEnabled, true)
            root.mediaControlsOpen = true
            compare(popupGate.popupEnabled, false)
            root.mediaControlsOpen = false
            controller.hasRememberedTrack = false
        }
        function test_media_hover_without_expansion_delay() {
            root.componentInteractionReady = false
            mouseMove(root, 380, 230)
            mouseMove(bar, 80, 16)
            tryCompare(root, "mediaHovered", true)
            wait(400)
            compare(root.mediaHovered, true)
            compare(root.componentInteractionReady, false)
            mouseMove(root, 380, 230)
            tryCompare(root, "mediaHovered", false)
        }
        function test_return_to_bar_keeps_popup_open() {
            bridge.targetHovered = true
            bridge.targetHovered = false
            bridge.popupHovered = true
            bridge.closeCalls = 0
            bridge.popupHovered = false
            wait(40)
            compare(bridge.shouldShow, true)
            bridge.barHovered = true
            bridge.targetHovered = true
            wait(100)
            compare(bridge.shouldShow, true)
            compare(bridge.closeCalls, 0)
            bridge.targetHovered = false
            bridge.barHovered = false
            wait(400)
            compare(bridge.shouldShow, false)
        }
        function test_bar_click_and_playback_controls() {
            for (const x of [16, 80, 190]) {
                const before = controller.raiseCalls
                mouseClick(bar, x, 16)
                compare(controller.raiseCalls, before + 1)
            }
            const before = controller.raiseCalls
            const buttons = mediaControlsRow.children
            mouseClick(buttons[0], 10, 10)
            compare(fakePlayer.previousCalls, 1)
            mouseClick(buttons[1], 11, 11)
            compare(controller.toggleCalls, 1)
            mouseClick(buttons[2], 10, 10)
            compare(fakePlayer.nextCalls, 1)
            compare(controller.raiseCalls, before)
        }
        function test_controls_keep_hover() {
            mouseMove(body, 10, 10)
            tryCompare(root, "popupHovered", true)
            mouseMove(play, play.width / 2, play.height / 2)
            compare(root.popupHovered, true)
            mouseClick(play)
            compare(root.popupHovered, true)
            mouseMove(progress, progress.width / 2, progress.height / 2)
            compare(root.popupHovered, true)
            mousePress(progress, 50, progress.height / 2)
            mouseMove(progress, 160, progress.height / 2)
            compare(root.popupHovered, true)
            mouseRelease(progress, 160, progress.height / 2)
            compare(root.popupHovered, true)
            mouseMove(root, 380, 230)
            tryCompare(root, "popupHovered", false)
        }
        function test_shared_artwork_and_color_updates() {
            root.artSourceOverride = Qt.resolvedUrl("cover.svg").toString()
            tryCompare(cover, "status", Image.Ready)
            root.artSourceOverride = ""
            compare(root.displayedArtFilePath, "")
            root.artUrl = ""
            root.artFilePath = "empty-track"
            colorQuantizer.colors = ["green"]
            compare(root.artDominantColor, Qt.color("green"))
            root.artSourceOverride = Qt.resolvedUrl("cover.svg").toString()
            tryCompare(cover, "status", Image.Ready)
            colorQuantizer.colors = ["purple"]
            compare(root.artDominantColor, Qt.color("purple"))
            root.downloaded = false
            root.artSourceOverride = undefined
            root.artFilePath = "no-art"
            colorQuantizer.colors = ["orange"]
            compare(root.artDominantColor, Qt.color("orange"))
        }
    }
}
'''.replace('TITLE_TEXT', title_text).replace('ARTIST_TEXT', artist_text).replace('PLAY_ACTION', play_action).replace('StringUtils.', 'stringUtils.').replace('POPUP_ENABLED', popup_enabled.replace('root.activePlayer', 'popupGate.activePlayer').replace('GlobalStates.', 'root.')).replace('MEDIA_ENABLED', media_enabled).replace('MEDIA_HOVER', media_hover).replace('BAR_CLICK', bar_click).replace('BAR_CONTROLS', bar_controls).replace('BRIDGE', bridge).replace('HOVER', hover).replace('OVERRIDE', art_override).replace('COLOR', color).replace('ART_PATH', art_path).replace('ART_CHANGED', art_changed).replace('Appearance', 'appearance').replace('ColorUtils', 'colorUtils').replace('MprisController.', 'controller.').replace('Config.', 'config.')
with tempfile.TemporaryDirectory(prefix='media-popup-check-') as directory:
    Path(directory, 'tst_popup.qml').write_text(qml)
    Path(directory, 'cover.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="4" height="4"><rect width="4" height="4" fill="red"/></svg>')
    subprocess.run(['/usr/lib/qt6/bin/qmltestrunner', '-input', directory],
                   env={**os.environ, 'QT_QPA_PLATFORM': 'offscreen', 'QT_QUICK_BACKEND': 'software',
                        'QT_QPA_PLATFORMTHEME': '', 'QT_QUICK_CONTROLS_STYLE': 'Basic'},
                   check=True, timeout=30)
