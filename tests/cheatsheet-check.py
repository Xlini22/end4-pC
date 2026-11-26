"""Run with python3 tests/cheatsheet-check.py (Qt 6 QtTest required)."""
import os
from pathlib import Path
import subprocess
import tempfile

repo = Path(__file__).resolve().parents[1]
source = (repo / 'modules/ii/cheatsheet/CheatsheetKeybinds.qml').read_text()
start = source.index('    readonly property var keybinds:')
end = source.index('    property real spacing:', start)
model = source[start:end].replace('HyprlandKeybinds.', 'dataSource.').replace('Translation.tr(', 'qsTr(')
start = source.index('                                        var result = [];')
end = source.index('                                        return result;', start) + len('                                        return result;')
render = source[start:end].replace('Config.options.cheatsheet.splitButtons', 'false')
qml = '''import QtQuick
import QtTest
Item {
    id: root
    property var keySubstitutions: ({SUPER: "Super"})
    property var keyBlacklist: []
    QtObject {
        id: dataSource
        property var defaultKeybinds: ({keybinds: [{mods: ["SUPER"], key: "H", comment: "Help"}],
            children: [{name: "Window", children: [{name: "Focus", keybinds: [
                {mods: ["ALT"], key: "Tab", comment: "Switch"}]}]}]})
        property var userKeybinds: ({keybinds: [{mods: ["CTRL"], key: "T", comment: "Custom"}]})
    }
    MODEL
    function renderKeys() {
        const keybindSection = {modelData: dataSource.defaultKeybinds};
        RENDER
    }
    TestCase {
        name: "RestoredCheatsheet"
        function test_sections_and_immutable_keys() {
            const sections = root.keybinds.children.reduce((all, column) => all.concat(column.children), []);
            compare(sections.length, 3);
            verify(sections.some(section => section.name === "Shell"));
            verify(sections.some(section => section.name === "Focus"));
            verify(sections.some(section => section.name === "Custom"));
            const original = JSON.stringify(dataSource.defaultKeybinds);
            const first = JSON.stringify(root.renderKeys());
            compare(JSON.stringify(root.renderKeys()), first);
            compare(JSON.stringify(dataSource.defaultKeybinds), original);
            dataSource.userKeybinds = {keybinds: [], children: []};
            compare(root.keybinds.children.reduce((all, column) => all.concat(column.children), []).length, 2);
        }
    }
}
'''.replace('MODEL', model).replace('RENDER', render)
with tempfile.TemporaryDirectory(prefix='cheatsheet-check-') as directory:
    Path(directory, 'tst_cheatsheet.qml').write_text(qml)
    subprocess.run(['/usr/lib/qt6/bin/qmltestrunner', '-input', directory],
                   env={**os.environ, 'QT_QPA_PLATFORM': 'offscreen',
                        'QT_QUICK_BACKEND': 'software', 'QT_QPA_PLATFORMTHEME': ''},
                   check=True, timeout=15)
