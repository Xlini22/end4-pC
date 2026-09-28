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
    property bool islandMode: false
    property bool islandExpanded: true
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
    readonly property int displayedBarCount: islandMode && !islandExpanded
        ? Math.max(1, Math.round(barCount / 3))
        : barCount

    function spectrumValue(barIndex) {
        if (root.points.length === 0) return 0
        if (root.displayedBarCount === root.barCount) {
            const sourceIndex = Math.floor(barIndex * root.points.length / root.barCount)
            return root.points[sourceIndex] ?? 0
        }

        // In compact mode each bar represents a complete frequency band, so
        // reducing the number of bars does not discard either end of the spectrum.
        const start = Math.floor(barIndex * root.points.length / root.displayedBarCount)
        const end = Math.max(start + 1,
            Math.floor((barIndex + 1) * root.points.length / root.displayedBarCount))
        let total = 0
        for (let i = start; i < Math.min(end, root.points.length); i++)
            total += root.points[i] ?? 0
        return total / Math.max(1, Math.min(end, root.points.length) - start)
    }

    readonly property real fullHorizontalWidth: isMaterial
        ? barCount * dotSize + (barCount - 1) * dotSpacing + 16
        : barCount * (dotSize + dotSpacing)
    readonly property real compactHorizontalWidth: displayedBarCount * dotSize
        + (displayedBarCount - 1) * dotSpacing
    implicitWidth: vertical
        ? Appearance.sizes.verticalBarWidth
        : (islandMode && !islandExpanded
            ? compactHorizontalWidth
            : fullHorizontalWidth)
    implicitHeight: vertical
        ? (isMaterial
            ? barsColumn.implicitHeight + 16
            : barCount * (dotSize + dotSpacing))
        : Appearance.sizes.barHeight
    clip: islandMode

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
            model: root.displayedBarCount
            Rectangle {
                required property int index
                width: root.dotSize
                property real pointValue: {
                    if (!root.isPlaying || root.points.length === 0) return root.dotSize
                    const v = root.spectrumValue(index)
                    return Math.max(root.dotSize, (v / root.maxVisualizerValue) * root.maxBarHeight)
                }
                height: pointValue
                radius: width / 2
                anchors.verticalCenter: parent.verticalCenter
                color: Appearance.colors.colOnLayer0
                opacity: root.isPlaying ? 0.85 : 0.3
                Behavior on height { NumberAnimation { duration: 80; easing.type: Easing.OutQuad } }
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
            model: root.displayedBarCount
            Rectangle {
                required property int index
                height: root.dotSize
                property real pointValue: {
                    if (!root.isPlaying || root.points.length === 0) return root.dotSize
                    const rawIndex = root.mirrored ? (root.displayedBarCount - 1 - index) : index
                    const v = root.spectrumValue(rawIndex)
                    return Math.max(root.dotSize, (v / root.maxVisualizerValue) * root.maxBarHeight)
                }
                width: pointValue
                radius: height / 2
                anchors.horizontalCenter: parent.horizontalCenter
                color: Appearance.colors.colPrimary
                opacity: root.isPlaying ? 0.85 : 0.3
                Behavior on width { NumberAnimation { duration: 80; easing.type: Easing.OutQuad } }
                Behavior on opacity { NumberAnimation { duration: 300 } }
            }
        }
    }
}
