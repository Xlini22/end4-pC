pragma ComponentBehavior: Bound

import qs.modules.common
import qs.modules.common.widgets
import qs.services
import QtQuick
import QtQuick.Layouts

Item {
    id: root

    property color textColor: "white"
    property color activeColor: "white"
    property color dimColor: Qt.rgba(1, 1, 1, 0.35)
    property color indicatorColor: Appearance.colors.colPrimaryContainer
    property color indicatorShapeColor: Appearance.colors.colOnPrimaryContainer
    property int textAlignment: Text.AlignLeft
    property bool compact: false
    property int firstSlot: 0
    property int slotCount: 7
    property real activeFontSize: compact
        ? Appearance.font.pixelSize.large : Appearance.font.pixelSize.normal
    property real adjacentFontSize: Appearance.font.pixelSize.small
    property real distantFontSize: Appearance.font.pixelSize.smaller
    property int displayedActiveIndex: LyricsService.activeIndex

    clip: true
    property real fontScale: 1.0
    property bool animateTransitions: false
    property real lineSpacing: 6

    implicitWidth: 200
    implicitHeight: 200

    Item {
        anchors.fill: parent

        Item {
            anchors.fill: parent
            visible: LyricsService.status === "loading"

            ColumnLayout {
                anchors.centerIn: parent
                spacing: 12

                Item {
                    Layout.alignment: Qt.AlignHCenter
                    implicitWidth: 48
                    implicitHeight: 48

                    MaterialLoadingIndicator {
                        anchors.fill: parent
                        loading: LyricsService.status === "loading"
                        colBg: root.indicatorColor
                        colShape: root.indicatorShapeColor
                        implicitSize: 48
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: LyricsService.restartLyrics()
                    }
                }
            }
        }

        ColumnLayout {
            id: lyricsList
            property real transitionOffset: 0
            property real transitionOpacity: 1

            anchors {
                left: parent.left
                right: parent.right
            }
            height: implicitHeight
            y: Math.round((parent.height - height) / 2) + transitionOffset
            opacity: transitionOpacity
            visible: LyricsService.status === "ok"
            spacing: root.compact ? 2 : root.lineSpacing

            Repeater {
                model: root.slotCount
                delegate: StyledText {
                    id: lyricSlot
                    required property int index
                    readonly property int slotIndex: root.firstSlot + index
                    Layout.fillWidth: true
                    horizontalAlignment: root.textAlignment
                    wrapMode: root.compact ? Text.NoWrap : Text.WordWrap
                    elide: root.compact ? Text.ElideRight : Text.ElideNone
                    maximumLineCount: root.compact ? 1 : 99
                    text: LyricsService.slots[slotIndex] ?? ""
                    readonly property int dist: Math.abs(slotIndex - LyricsService.before)
                    font.pixelSize: {
                        if (dist === 0) return root.activeFontSize * root.fontScale
                        if (dist === 1) return root.adjacentFontSize * root.fontScale
                        return root.distantFontSize * root.fontScale
                    }
                    opacity: {
                        if (dist === 0) return 1.0
                        if (dist === 1) return 0.6
                        if (dist === 2) return 0.35
                        return 0.15
                    }
                    color: dist === 0 ? root.activeColor : root.textColor
                    transform: Translate { id: lineSlide }
                    onTextChanged: {
                        if (root.animateTransitions) slideAnim.restart();
                    }
                    SequentialAnimation {
                        id: slideAnim
                        ScriptAction { script: lineSlide.y = 28 * root.fontScale }
                        NumberAnimation { target: lineSlide; property: "y"; to: 0; duration: 420; easing.type: Easing.OutBack }
                    }
                    Behavior on font.pixelSize {
                        enabled: root.animateTransitions
                        NumberAnimation { duration: 300; easing.type: Easing.OutCubic }
                    }
                    Behavior on opacity { NumberAnimation { duration: 250; easing.type: Easing.OutCubic } }
                }
            }
        }

        ParallelAnimation {
            id: lineChangeAnimation

            NumberAnimation {
                target: lyricsList
                property: "transitionOffset"
                to: 0
                duration: 300
                easing.type: Easing.OutCubic
            }

            NumberAnimation {
                target: lyricsList
                property: "transitionOpacity"
                to: 1
                duration: 220
                easing.type: Easing.OutCubic
            }
        }

        Connections {
            target: LyricsService

            function onActiveIndexChanged() {
                const nextIndex = LyricsService.activeIndex
                const previousIndex = root.displayedActiveIndex
                root.displayedActiveIndex = nextIndex

                if (previousIndex < 0 || nextIndex < 0 || previousIndex === nextIndex)
                    return

                const direction = nextIndex > previousIndex ? 1 : -1
                Qt.callLater(() => {
                    lineChangeAnimation.stop()
                    lyricsList.transitionOffset = direction
                        * (root.compact ? 18 : 30)
                    lyricsList.transitionOpacity = 0.55
                    lineChangeAnimation.start()
                })
            }
        }
    }
}
