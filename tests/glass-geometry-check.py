"""Run: python3 tests/glass-geometry-check.py (QtTest, software rendering only)."""
import os
from pathlib import Path
import subprocess
import tempfile

source = (Path(__file__).resolve().parents[1] / 'modules/common/widgets/WindowGlass.qml').read_text()
geometry = source[source.index('    property var ancestorTransforms:'):source.index('    onTrackingChanged:')]
refresh = source[source.index('    function refresh()'):source.index('    function kick()')]
qml = '''import QtQuick
import QtTest
Item {
    id: scene
    width: 800; height: 600
    Item {
        id: first
        x: 20; y: 30
        transform: Scale { id: firstScale; xScale: 1; yScale: 1 }
        Item {
            id: root
            width: 100; height: 80
            property bool tracking: true
            property bool trackGeometry: true
            property bool enhancedNative: false
            property rect sceneRect: Qt.rect(0, 0, width, height)
            property int updates: 0
            function kick() { updates++; refresh() }
            REFRESH
            GEOMETRY
            Component.onCompleted: { syncAncestorTransforms(); refresh() }
        }
    }
    Item {
        id: second
        x: 400; y: 200
        transform: Scale { id: secondScale; xScale: 2; yScale: 2 }
    }
    NumberAnimation {
        id: expand
        target: firstScale; property: "xScale"
        from: 1; to: 1.8; duration: 200
    }
    TestCase {
        name: "GlassGeometry"
        when: windowShown
        function init() { failOnWarning(/.*/) }
        function test_01_transforms() {
            tryCompare(root, "ancestorTransforms", [firstScale])
            firstScale.xScale = .5
            firstScale.yScale = .75
            tryCompare(root, "sceneRect", Qt.rect(20, 30, 50, 60))
            first.x = 40
            tryCompare(root, "sceneRect", Qt.rect(40, 30, 50, 60))
            first.opacity = .5
            const before = root.updates
            first.opacity = 1
            verify(root.updates > before, "Ancestor opacity still updates native regions")
            firstScale.xScale = 1
            firstScale.yScale = 1
            expand.start()
            wait(90)
            verify(root.sceneRect.width > 100 && root.sceneRect.width < 180)
            tryCompare(expand, "running", false)
            verify(Math.abs(root.sceneRect.width - 180) < .001)
        }
        function test_02_reparent() {
            root.parent = second
            tryCompare(root, "ancestorTransforms", [secondScale])
            tryCompare(root, "sceneRect", Qt.rect(400, 200, 200, 160))
            secondScale.xScale = .5
            tryCompare(root, "sceneRect", Qt.rect(400, 200, 50, 160))
            const before = root.updates
            firstScale.xScale = 3
            wait(30)
            compare(root.updates, before, "Old ancestors are no longer watched")
        }
        function test_03_tracking() {
            root.tracking = false
            tryCompare(root, "ancestorTransforms", [])
            const before = root.updates
            secondScale.xScale = 1.5
            wait(30)
            compare(root.updates, before)
            root.tracking = true
            tryCompare(root, "ancestorTransforms", [secondScale])
            tryCompare(root, "sceneRect", Qt.rect(400, 200, 150, 160))
            root.trackGeometry = false
            tryCompare(root, "ancestorTransforms", [])
            root.trackGeometry = true
            tryCompare(root, "ancestorTransforms", [secondScale])
        }
    }
}
'''.replace('GEOMETRY', geometry).replace('REFRESH', refresh)
with tempfile.TemporaryDirectory(prefix='glass-geometry-') as directory:
    Path(directory, 'tst_geometry.qml').write_text(qml)
    result = subprocess.run(['/usr/lib/qt6/bin/qmltestrunner', '-input', directory],
                   env={**os.environ, 'QT_QPA_PLATFORM': 'offscreen', 'QT_QUICK_BACKEND': 'software',
                        'QT_QPA_PLATFORMTHEME': ''}, capture_output=True, text=True, timeout=15)
    output = result.stdout + result.stderr
    assert result.returncode == 0 and 'QWARN' not in output, output
    print(output, end='')
