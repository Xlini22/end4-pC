import QtQuick
import QtQuick.Layouts
import Quickshell.Io
import Quickshell.Services.Mpris
import qs
import qs.services
import qs.modules.common
import qs.modules.common.widgets

Item {
    id: root
    property bool vertical: Config.options.bar.vertical
    property bool isMaterial: Config.options.bar.cornerStyle === 3
    property bool mirrored: false
    readonly property MprisPlayer activePlayer: MprisController.activePlayer
    readonly property bool isPlaying: activePlayer?.isPlaying ?? false
    readonly property list<real> points: GlobalStates.visualizerPoints
    property int barCount: 20
    property real dotSize: 3
    property real dotSpacing: 3
    property real maxBarHeight: (vertical
        ? Appearance.sizes.verticalBarWidth
        : Appearance.sizes.barHeight) * 0.7
    property real maxVisualizerValue: 1000
    property color barColor: Appearance.colors.colPrimary
    property bool frameSmoothing: false
    property list<real> smoothedPoints: []

    FrameAnimation {
        running: root.frameSmoothing && root.isPlaying
        onTriggered: {
            const dt = Math.min(frameTime, 0.05)
            const values = new Array(root.barCount)
            for (let i = 0; i < root.barCount; i++) {
                const sourceIndex = Math.floor(i * root.points.length / root.barCount)
                const target = root.points.length > 0 ? (root.points[sourceIndex] ?? 0) : 0
                const current = root.smoothedPoints[i] ?? 0
                const speed = target > current ? 22 : 10
                values[i] = current + (target - current) * Math.min(1, dt * speed)
            }
            root.smoothedPoints = values
        }
    }

    implicitWidth: vertical
        ? Appearance.sizes.verticalBarWidth
        : (isMaterial
            ? barsRow.implicitWidth + 16
            : barCount * (dotSize + dotSpacing))
    implicitHeight: vertical
        ? (isMaterial
            ? barsColumn.implicitHeight + 16
            : barCount * (dotSize + dotSpacing))
        : Appearance.sizes.barHeight

    transform: Scale {
        xScale: !root.vertical && root.mirrored ? -1 : 1
        origin.x: root.width / 2
    }


    Row {
        id: barsRow
        visible: !root.vertical
        anchors.centerIn: parent
        spacing: root.dotSpacing

        Repeater {
            model: root.barCount
            Rectangle {
                required property int index
                width: root.dotSize
                property real pointValue: {
                    if (!root.isPlaying || root.points.length === 0) return root.dotSize
                    const idx = Math.floor(index * root.points.length / root.barCount)
                    const v = root.frameSmoothing
                        ? (root.smoothedPoints[index] ?? 0)
                        : (root.points[idx] ?? 0)
                    return Math.max(root.dotSize, (v / root.maxVisualizerValue) * root.maxBarHeight)
                }
                height: pointValue
                radius: width / 2
                anchors.verticalCenter: parent.verticalCenter
                color: Appearance.colors.colPrimary
                opacity: root.isPlaying ? 0.85 : 0.3
                Behavior on height {
                    enabled: !root.frameSmoothing
                    NumberAnimation { duration: 80; easing.type: Easing.OutQuad }
                }
                Behavior on opacity { NumberAnimation { duration: 300 } }
            }
        }
    }

    Column {
        id: barsColumn
        visible: root.vertical
        anchors.centerIn: parent
        spacing: root.dotSpacing

        Repeater {
            model: root.barCount
            Rectangle {
                required property int index
                height: root.dotSize
                property real pointValue: {
                    if (!root.isPlaying || root.points.length === 0) return root.dotSize
                    const rawIndex = root.mirrored ? (root.barCount - 1 - index) : index
                    const idx = Math.floor(rawIndex * root.points.length / root.barCount)
                    const v = root.frameSmoothing
                        ? (root.smoothedPoints[rawIndex] ?? 0)
                        : (root.points[idx] ?? 0)
                    return Math.max(root.dotSize, (v / root.maxVisualizerValue) * root.maxBarHeight)
                }
                width: pointValue
                radius: height / 2
                anchors.horizontalCenter: parent.horizontalCenter
                color: Appearance.colors.colPrimary
                opacity: root.isPlaying ? 0.85 : 0.3
                Behavior on width {
                    enabled: !root.frameSmoothing
                    NumberAnimation { duration: 80; easing.type: Easing.OutQuad }
                }
                Behavior on opacity { NumberAnimation { duration: 300 } }
            }
        }
    }
}
