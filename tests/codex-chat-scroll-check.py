"""Run python3 tests/codex-chat-scroll-check.py; no account or network is used."""
import os
from pathlib import Path
import subprocess
import tempfile

repo = Path(__file__).resolve().parents[1]
source = (repo / 'modules/ii/sidebarLeft/CodexChat.qml').read_text()
start = source.index('        ListView {\n            id: conversation')
end = source.index('\n            delegate: Item {', start)
view = source[start:end].replace('Codex.messageGroups', 'testModel').replace('StyledScrollBar', 'ScrollBar').replace('Config.', 'TestConfig.')
view += '\n delegate: Rectangle { required property int rowHeight; width: conversation.width; height: rowHeight }\n}'
popup_start = source.index('        Popup {\n            id: settingsPopup')
popup_end = source.index('            background: Rectangle {', popup_start)
popup = source[popup_start:popup_end] + '\n contentItem: Rectangle { implicitHeight: 150; implicitWidth: 300 }\n}'
countdown_start = source.index('    function resetCountdown(')
countdown_end = source.index('\n    }', countdown_start) + len('\n    }')
countdown = source[countdown_start:countdown_end]
harness = '''import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import Quickshell
import "."
ShellRoot {
 id: test
 property int phase: 0
 property bool failed: false
 property real readingY: 0
 property real viewportHeight: 0
 COUNTDOWN
 ListModel { id: testModel }
 Window { id: root; visible: true; width: 360; height: 300
  ColumnLayout { anchors.fill: parent; anchors.margins:16
   RowLayout { Layout.fillWidth:true
    Item { Layout.fillWidth:true }
    Button { id:settingsToggle; text:"Settings"; checkable:true }
   }
   SETTINGS
   VIEW
  }
 }
 function check(value, message) {
  if (!value) { failed = true; console.error("CHECK FAILED: " + message); Qt.quit(); }
 }
 Component.onCompleted: {
  for (let i = 0; i < 80; i++) testModel.append({rowHeight: 40 + (i % 5) * 25});
 }
 Timer { interval: 250; repeat: true; running: true
  onTriggered: {
   if (test.failed) return;
   if (test.phase === 0) {
    test.check(test.resetCountdown(3600, 0) === "Reset tra 1h 0min", "hour countdown");
    test.check(test.resetCountdown(90000, 0) === "Reset tra 1g 1h", "weekly countdown");
    test.check(test.resetCountdown(60, 0) === "Reset tra 1 min", "minute countdown");
    test.check(test.resetCountdown(60, 60000) === "Reset in aggiornamento…", "expired quota waits for server refresh");
    test.check(test.resetCountdown(undefined, 0) === "Reset non disponibile", "missing reset time");
    conversation.followOutput = true;
    conversation.followLatest();
   } else if (test.phase === 1) {
    test.check(conversation.atYEnd, "initial history follows the latest message");
    chatTouchpad.handleWheel({angleDelta:{x:0,y:12},pixelDelta:{x:0,y:120},accepted:false});
    test.check(!conversation.followOutput, "touchpad immediately suspends automatic following");
    testModel.append({rowHeight:300});
   } else if (test.phase === 2) {
    test.check(!conversation.atYEnd, "content height changes must not pull a touchpad reader to the bottom");
    conversation.followOutput = true;
    conversation.contentHeightChanged();
    conversation.followOutput = false;
    conversation.positionViewAtBeginning();
   } else if (test.phase === 3) {
    test.check(conversation.atYBeginning, "a queued follow must recheck user intent before moving");
    conversation.positionViewAtEnd();
   } else if (test.phase === 4) {
    conversation.forceLayout();
    conversation.positionViewAtEnd();
    conversation.movementEnded();
    test.check(conversation.followOutput, "returning to the bottom resumes following");
    testModel.append({rowHeight:180});
   } else if (test.phase === 5) {
    test.check(conversation.atYEnd, "new output follows when the user is at the bottom");
    chatScrollBar.pressed = true;
    test.check(!conversation.followOutput, "dragging the scrollbar suspends following");
    conversation.positionViewAtBeginning();
    testModel.append({rowHeight:220});
   } else if (test.phase === 6) {
    test.check(conversation.atYBeginning, "scrollbar reading position survives new output");
    chatScrollBar.pressed = false;
    test.check(!conversation.followOutput, "releasing scrollbar away from bottom keeps reading position");
    test.readingY = conversation.contentY;
    test.viewportHeight = conversation.height;
    settingsToggle.checked = true;
   } else if (test.phase === 7) {
    test.check(settingsPopup.opened, "settings dropdown opens");
    test.check(conversation.height === test.viewportHeight && conversation.contentY === test.readingY, "opening settings must not resize or shift chat");
    settingsToggle.checked = false;
   } else if (test.phase === 8) {
    test.check(!settingsPopup.opened && conversation.height === test.viewportHeight && conversation.contentY === test.readingY, "closing settings preserves reading position");
    console.log("CODEX CHAT SCROLL PASSED"); Qt.quit();
   }
   test.phase++;
  }
 }
 Timer { interval:8000; running:true; onTriggered:{ console.error("CHECK TIMED OUT"); Qt.quit(); } }
}'''.replace('VIEW', view).replace('COUNTDOWN', countdown).replace('SETTINGS', popup)
with tempfile.TemporaryDirectory(prefix='codex-chat-scroll-') as directory:
    temporary = Path(directory)
    (temporary / 'shell.qml').write_text(harness)
    touchpad = (repo / 'modules/common/widgets/TouchpadScrollArea.qml').read_text()
    (temporary / 'TouchpadScrollArea.qml').write_text(touchpad.replace('import qs.modules.common', 'import "."').replace('Config.', 'TestConfig.'))
    (temporary / 'qmldir').write_text('singleton TestConfig 1.0 TestConfig.qml\nTouchpadScrollArea 1.0 TouchpadScrollArea.qml\n')
    (temporary / 'TestConfig.qml').write_text('''pragma Singleton
import QtQuick
QtObject { property var options: ({interactions:{scrolling:{fasterTouchpadScroll:false,touchpadScrollFactor:1,touchpadSensitivity:1}}}) }
''')
    runtime = temporary / 'runtime'
    runtime.mkdir(mode=0o700)
    result = subprocess.run(['qs', '--no-color', '-p', str(temporary / 'shell.qml')], capture_output=True,
        text=True, timeout=15, env={**os.environ, 'QT_QPA_PLATFORM':'offscreen', 'QT_QUICK_BACKEND':'software',
                                 'QT_QPA_PLATFORMTHEME':'', 'XDG_RUNTIME_DIR':str(runtime)})
    output = result.stdout + result.stderr
    assert result.returncode == 0 and 'CODEX CHAT SCROLL PASSED' in output, output
    assert not any(error in output for error in ['CHECK FAILED', 'TypeError', 'ReferenceError', 'Binding loop']), output
    print('Codex chat: touchpad, queued following, streaming and scrollbar reading position passed')
