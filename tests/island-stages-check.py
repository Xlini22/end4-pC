"""Run with python3 tests/island-stages-check.py (Qt 6 QtTest required).
Exercise the production delegates and widget layouts with fixed service data.
"""
import os
import re
from pathlib import Path
import subprocess
import tempfile

repo = Path(__file__).resolve().parents[1]
bar = repo / 'modules/ii/bar'
source = (bar / 'DynamicIsland.qml').read_text()
curve = re.search(r'expressiveDefaultSpatial: (\[[^\]]+\])',
                  (repo / 'modules/common/Appearance.qml').read_text())[1]
start = source.index('    component SideWidgetDelegate:')
delegate = source[start:source.index('    component SideWidgets:', start)]
delegate = delegate.replace('        required property bool anchorRight', '''        required property bool anchorRight
        readonly property var testContent: modelData === "media" ? mediaLoader.item : regularLoader.item
        readonly property real testContentX: modelData === "media" ? mediaLoader.x : regularLoader.x''')
media_start = source.index('        Item {\n            id: mediaSideRoot')
media_item = source[media_start:source.index('            HoverHandler {', media_start)] + '\n        }'
qml = '''import QtQuick
import QtQuick.Layouts
import QtTest
Item {
    id: root
    width: leftRow.width + rightRow.width + 40; height: 80
    property bool expanded: false
    property bool hasMedia: true
    property bool hasActiveActivity: false
    property var activePlayer: ({isPlaying: true})
    property bool mediaTrackInfoVisible: expanded
    property real mediaCollapsedWidth: 60
    property real mediaWidth: mediaTrackInfoVisible ? mediaExpandedWidth : mediaCollapsedWidth
    property real mediaExpandedWidth: 180
    property bool componentInteractionReady: true
    property real pillHeight: 32
    QtObject { id: mediaSideHover; property bool hovered: false }
    Component { id: mediaSideComponent; MEDIA_ITEM }
    Component { id: activitySideComponent; Item {} }
    DELEGATE
    Row {
        id: leftRow
        anchors.left: parent.left
        spacing: 8
        SideWidgetDelegate { id: leftClock; modelData: "clockWidget"; anchorRight: false }
        SideWidgetDelegate { id: leftResources; modelData: "resources"; anchorRight: false }
        SideWidgetDelegate { id: leftVisualizer; modelData: "visualizer"; anchorRight: false }
        SideWidgetDelegate { id: leftMedia; modelData: "media"; anchorRight: false }
    }
    Row {
        id: rightRow
        anchors.right: parent.right
        y: 40
        spacing: 8
        SideWidgetDelegate { id: rightClock; modelData: "clockWidget"; anchorRight: true }
        SideWidgetDelegate { id: rightResources; modelData: "resources"; anchorRight: true }
        SideWidgetDelegate { id: rightVisualizer; modelData: "visualizer"; anchorRight: true }
        SideWidgetDelegate { id: rightMedia; modelData: "media"; anchorRight: true }
    }
    TestCase {
        name: "IslandStages"
        when: windowShown
        function initTestCase() { failOnWarning(/.*/) }
        function test_phases_data() {
            return [{tag: "default", cornerStyle: 0}, {tag: "material", cornerStyle: 3}]
        }
        function rightEdge(widget) { return widget.mapToItem(root, widget.width, 0).x }
        function leftEdge(widget) { return widget.mapToItem(root, 0, 0).x }
        function test_phases(data) {
            Config.cornerStyle = data.cornerStyle
            root.expanded = false
            tryCompare(rightClock, "layoutProgress", 0)
            wait(50)
            const clocks = [leftClock, rightClock]
            const resources = [leftResources, rightResources]
            const widgets = clocks.concat(resources, [leftVisualizer, rightVisualizer, leftMedia, rightMedia])
            const compactWidths = widgets.map(widget => widget.testContent.width)
            const initialWidth = root.width
            root.expanded = true
            wait(150)
            verify(root.width > initialWidth)
            widgets.forEach((widget, i) => {
                compare(widget.testContent.width, compactWidths[i], "Phase 1 keeps the real widget compact")
                compare(widget.revealProgress, 0)
                verify(widget.layoutProgress > 0.4 && widget.layoutProgress < 0.6,
                    "The first movement ends near the midpoint")
                compare(widget.testContentX, widget.anchorRight ? widget.width - compactWidths[i] : 0)
            })
            wait(220)
            widgets.forEach(widget => compare(widget.layoutProgress, 1))
            wait(20)
            const finalBarWidth = root.width
            const edges = widgets.map(widget => widget.anchorRight ? rightEdge(widget) : leftEdge(widget))
            wait(100)
            widgets.forEach((widget, i) => {
                verify(widget.testContent.width > compactWidths[i], "Phase 2 expands the actual widget")
                compare(widget.testContentX, widget.anchorRight ? widget.width - widget.testContent.width : 0)
                verify(Math.abs((widget.anchorRight ? rightEdge(widget) : leftEdge(widget)) - edges[i]) < 0.01,
                    "The slot stays in its final position during phase 2")
            })
            verify(Math.abs(root.width - finalBarWidth) < 0.01, "The bar has already finished expanding")
            widgets.forEach(widget => tryCompare(widget, "revealProgress", 1))
            wait(20)
            widgets.forEach(widget => {
                compare(widget.width, widget.expandedContentWidth)
                verify(Math.abs(widget.width - widget.testContent.width) < 1,
                    "The reserved width matches the fully expanded widget")
            })
            verify(Math.abs(root.width - finalBarWidth) < 0.01)
            root.expanded = false
            wait(150)
            widgets.forEach(widget => compare(widget.layoutProgress, 1))
            widgets.forEach(widget => tryCompare(widget, "layoutProgress", 0))
            for (let i = 0; i < 30; ++i) {
                root.expanded = !root.expanded
                wait(8)
            }
            root.expanded = false
            widgets.forEach((widget, i) => {
                tryCompare(widget, "revealProgress", 0)
                tryCompare(widget, "layoutProgress", 0)
                compare(widget.testContent.width, compactWidths[i])
            })
        }
    }
}
'''.replace('DELEGATE', delegate).replace('MEDIA_ITEM', media_item)

singletons = {
    'Config': '''property int cornerStyle: 0
        property var options: ({bar: {cornerStyle: cornerStyle, borderless: false, vertical: false,
            tooltips: {clickToShow: false}, dynamicIsland: {animationStyle: "staged", widgetModes: {}},
            resources: {showValue: true, style: "outline", alwaysShowRam: true, alwaysShowCpu: true,
                alwaysShowCpuTemp: true, alwaysShowDisk: true, alwaysShowSwap: true,
                memoryWarningThreshold: 100, cpuWarningThreshold: 100, swapWarningThreshold: 100}},
            time: {showDate: true}})''',
    'Appearance': '''property var colors: ({colOnLayer0: "white", colOnLayer1: "white",
        colOnSecondaryContainer: "white", colPrimary: "white", colOnPrimary: "black",
        colError: "red", colOnPrimaryContainer: "white", colTertiaryContainer: "gray"})
        property var sizes: ({barHeight: 32, verticalBarWidth: 32})
        property var rounding: ({full: 20, unsharpen: 1})
        property var font: ({pixelSize: {small: 15, smaller: 13, smallie: 14, normal: 16}})
        property Component movement: NumberAnimation { duration: 100 }
        property var animation: ({elementMove: {numberAnimation: movement}})
        property var animationCurves: ({expressiveDefaultSpatial: [0, 0, 0.2, 1, 1, 1]})''',
    'DateTime': '''property string time: "12:34"
        property string longDate: "Monday, October 5"
        function format(value, format) { return "12:34" }''',
    'MprisController': 'property var activePlayer: null',
    'GlobalStates': 'property list<real> visualizerPoints: [100, 200, 400]',
    'ResourceUsage': '''property int consumers: 0
        property real memoryUsedPercentage: 0.4
        property real cpuUsage: 0.3
        property real cpuTemp: 40
        property real diskUsedPercentage: 0.5
        property real swapUsedPercentage: 0.1''',
}
with tempfile.TemporaryDirectory(prefix='island-stages-check-') as directory:
    target = Path(directory)
    singletons['Appearance'] = re.sub(r'expressiveDefaultSpatial: \[[^\]]+\]',
                                       'expressiveDefaultSpatial: ' + curve, singletons['Appearance'])
    target.joinpath('qmldir').write_text('\n'.join(f'singleton {name} 1.0 {name}.qml' for name in singletons))
    for name, properties in singletons.items():
        target.joinpath(f'{name}.qml').write_text('pragma Singleton\nimport QtQuick\nQtObject {\n' + properties + '\n}')
    for name, folder in [('ClockWidget', bar), ('Resources', bar), ('Resource', bar), ('Visualizer', bar),
                         ('BarWidgetSwitcher', repo / 'modules/common/widgets'),
                         ('BarWidgetSwitcherArea', repo / 'modules/common/widgets')]:
        original = (folder / f'{name}.qml').read_text()
        original = original.replace('readonly property MprisPlayer activePlayer:', 'readonly property var activePlayer:')
        target.joinpath(f'{name}.qml').write_text('\n'.join(line for line in original.splitlines()
                                                        if not line.startswith(('import qs', 'import Quickshell'))))
    target.joinpath('StyledText.qml').write_text('import QtQuick\nText { font.family: "Sans" }')
    target.joinpath('MaterialSymbol.qml').write_text('import QtQuick\nText { property int fill: 0; property int iconSize: 16 }')
    for name in ['ClockWidgetPopup', 'ResourcesPopup']:
        target.joinpath(f'{name}.qml').write_text('import QtQuick\nItem { property var hoverTarget; property var today }')
    for name in ['ClippedOutlineCircularProgress', 'ClippedFilledCircularProgress']:
        target.joinpath(f'{name}.qml').write_text('''import QtQuick
Item { property real lineWidth: 1; property real value: 0; property real implicitSize: 20
    property color colPrimary: "white"; property bool enableAnimation: false
    property bool accountForLightBleeding: false
    implicitWidth: implicitSize; implicitHeight: implicitSize }''')
    target.joinpath('tst_stages.qml').write_text(qml)
    subprocess.run(['/usr/lib/qt6/bin/qmltestrunner', '-input', directory],
                   env={**os.environ, 'QT_QPA_PLATFORM': 'offscreen', 'QT_QUICK_BACKEND': 'software',
                        'QT_QPA_PLATFORMTHEME': ''}, check=True, timeout=20)
