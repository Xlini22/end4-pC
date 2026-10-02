"""Run with python3 tests/lock-media-controls-check.py (Qt 6 QtTest required)."""
import os
from pathlib import Path
import subprocess
import tempfile

source = (Path(__file__).resolve().parents[1] / 'modules/ii/lock/LockSurface.qml').read_text()
start = source.index('                    Item {\n                        Layout.alignment: Qt.AlignVCenter\n                        Layout.leftMargin: -mediaRow.spacing')
controls = source[start:source.index('                    ClippedFilledCircularProgress {', start)]
start = source.index('                property real controlsReveal:')
reveal = source[start:source.index('                readonly property string cleanedTitle:', start)]
# Exercise the production controls with a fake player, without locking the session.
qml = '''import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtTest

Item {
    width: 420; height: 100
    QtObject {
        id: player
        property bool canGoPrevious: true
        property bool canGoNext: true
        property bool canTogglePlaying: true
        property bool isPlaying: true
        property int previousCalls: 0
        property int nextCalls: 0
        function previous() { previousCalls++ }
        function next() { nextCalls++ }
    }
    QtObject {
        id: controller
        function togglePlaying() { player.isPlaying = !player.isPlaying }
    }
    QtObject {
        id: translation
        function tr(value) { return value }
    }
    QtObject {
        id: appearance
        property var colors: ({colOnSurfaceVariant: "white"})
        property var animation: ({elementMove: {numberAnimation: animationFactory}})
    }
    Component { id: animationFactory; NumberAnimation { duration: 40 } }
    component RippleButton: Button { property real buttonRadius }
    component MaterialSymbol: Text { property real fill; property real iconSize }
    Rectangle {
        id: pill
        x: 10; y: 10; height: 50
        width: 120 + lockMedia.implicitWidth
        HoverHandler { id: mediaHover }
        Item {
            id: lockMedia
            x: 120
            property var activePlayer: player
            implicitWidth: mediaRow.implicitWidth
            implicitHeight: 28
            REVEAL
            RowLayout {
                id: mediaRow
                spacing: 8
                CONTROLS
            }
        }
    }
    TestCase {
        name: "LockMediaControls"
        when: windowShown
        function test_hover_and_actions() {
            mouseMove(pill, 20, 20)
            tryCompare(lockMedia, "controlsReveal", 1)
            verify(pill.width > 120)
            const buttons = lockControls.children
            compare(buttons.length, 3)
            mouseClick(buttons[0], 14, 14)
            compare(player.previousCalls, 1)
            mouseClick(buttons[1], 14, 14)
            compare(player.isPlaying, false)
            mouseClick(buttons[2], 14, 14)
            compare(player.nextCalls, 1)
            compare(lockMedia.controlsReveal, 1)
            player.canGoNext = false
            compare(buttons[2].enabled, false)
            mouseMove(pill, 350, 70)
            tryCompare(lockMedia, "controlsReveal", 0)
            compare(pill.width, 120)
            compare(mediaRow.children[0].enabled, false)
        }
    }
}
'''.replace('REVEAL', reveal).replace('CONTROLS', controls).replace('MprisController.', 'controller.').replace('Translation.', 'translation.').replace('Appearance.', 'appearance.')
with tempfile.TemporaryDirectory(prefix='lock-media-check-') as directory:
    Path(directory, 'tst_controls.qml').write_text(qml)
    subprocess.run(['/usr/lib/qt6/bin/qmltestrunner', '-input', directory],
                   env={**os.environ, 'QT_QPA_PLATFORM': 'offscreen', 'QT_QUICK_BACKEND': 'software',
                        'QT_QPA_PLATFORMTHEME': '', 'QT_QUICK_CONTROLS_STYLE': 'Basic'},
                   check=True, timeout=30)
