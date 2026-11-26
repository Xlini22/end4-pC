"""Run: python3 tests/sidebar-shortcut-check.py (Qt 6 QtTest required)."""
import os
from pathlib import Path
import subprocess
import tempfile

source = (Path(__file__).resolve().parents[1] / 'modules/ii/sidebarLeft/SidebarLeft.qml').read_text()
start = source.index('                Keys.onPressed:')
end = source.index('\n            }\n        }\n    }\n\n    Loader', start)
handlers = source[start:end].replace('Codex.', 'codex.')
qml = '''import QtQuick
import QtQuick.Controls.Basic
import QtTest
Item {
    id: root
    width: 400; height: 300
    property bool open: true
    property bool preview: false
    function toggleDetach() {}
    function togglePin() {}
    QtObject { id: codex; property bool fileDialogOpen: false }
    Item {
        id: panelWindow
        anchors.fill: parent
        property bool extend: false
        function hide() { root.open = false }
        Item {
            anchors.fill: parent
            HANDLERS
            TextArea { id: input; width: 200; height: 80 }
            Button { id: button; y: 90; text: "Page" }
            Item {
                id: consumer
                Keys.onPressed: event => { event.accepted = true }
            }
        }
    }
    TestCase {
        name: "SidebarExpandShortcut"
        when: windowShown
        function init() {
            root.open = true
            root.preview = false
            codex.fileDialogOpen = false
            panelWindow.extend = false
        }
        function test_focus_data() {
            return [{tag: "text", item: input}, {tag: "button", item: button},
                    {tag: "consumed key", item: consumer}]
        }
        function test_focus(data) {
            data.item.forceActiveFocus()
            verify(data.item.activeFocus)
            keyClick(Qt.Key_O, Qt.ControlModifier)
            compare(panelWindow.extend, true)
            keyClick(Qt.Key_O, Qt.ControlModifier)
            compare(panelWindow.extend, false)
        }
        function test_disabled_data() {
            return [{tag: "closed"}, {tag: "preview"}, {tag: "file dialog"}]
        }
        function test_disabled(data) {
            consumer.forceActiveFocus()
            root.open = data.tag !== "closed"
            root.preview = data.tag === "preview"
            codex.fileDialogOpen = data.tag === "file dialog"
            keyClick(Qt.Key_O, Qt.ControlModifier)
            compare(panelWindow.extend, false)
        }
        function test_other_keys() {
            input.forceActiveFocus()
            keyClick(Qt.Key_O)
            compare(input.text, "o")
            compare(panelWindow.extend, false)
            keyClick(Qt.Key_O, Qt.ControlModifier | Qt.ShiftModifier)
            compare(panelWindow.extend, false)
        }
    }
}
'''.replace('HANDLERS', handlers)
with tempfile.TemporaryDirectory(prefix='sidebar-shortcut-') as directory:
    Path(directory, 'tst_shortcut.qml').write_text(qml)
    subprocess.run(['/usr/lib/qt6/bin/qmltestrunner', '-input', directory],
                   env={**os.environ, 'QT_QPA_PLATFORM': 'offscreen',
                        'QT_QUICK_BACKEND': 'software', 'QT_QPA_PLATFORMTHEME': ''},
                   check=True, timeout=20)
