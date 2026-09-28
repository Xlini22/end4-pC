pragma ComponentBehavior: Bound

import qs.modules.common
import qs.modules.common.models
import qs.modules.common.widgets
import qs.services
import qs.modules.common.functions
import Qt5Compat.GraphicalEffects
import QtQuick
import QtQuick.Layouts
import Quickshell.Services.Mpris

Item {
    id: root

    required property MprisPlayer player
    required property QtObject blendedColors
    required property string displayedArtFilePath
    required property real radius
    required property color artDominantColor
    property bool useSharedTimeline: false
    readonly property real playbackPosition: useSharedTimeline
        ? MediaArtwork.playbackPosition : Number(player?.position ?? 0)
    readonly property real playbackLength: useSharedTimeline
        ? MediaArtwork.playbackLength : Number(player?.length ?? 0)
    readonly property bool playbackLengthKnown: useSharedTimeline
        ? MediaArtwork.durationKnown : playbackLength > 0
    signal toggleLyrics()

    RowLayout {
        anchors.fill: parent
        anchors.margins: 13
        spacing: 15

        Item {
            Layout.fillHeight: true
            Layout.preferredWidth: height
            Layout.maximumWidth: height
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 2

            RowLayout {
                Layout.fillWidth: true
                spacing: 6

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: -2

                    StyledText {
                        Layout.fillWidth: true
                        font.pixelSize: Appearance.font.pixelSize.large
                        color: root.blendedColors.colOnLayer0
                        elide: Text.ElideRight
                        text: StringUtils.cleanMusicTitle(root.player?.trackTitle) || "Untitled"
                        animateChange: true
                        animationDistanceX: 6
                        animationDistanceY: 0

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: MprisController.raiseActivePlayer()
                        }
                    }

                    StyledText {
                        Layout.fillWidth: true
                        font.pixelSize: Appearance.font.pixelSize.smaller
                        color: root.blendedColors.colSubtext
                        elide: Text.ElideRight
                        text: root.player?.trackArtist ?? ""
                        animateChange: true
                        animationDistanceX: 6
                        animationDistanceY: 0

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: MprisController.raiseActivePlayer()
                        }
                    }
                }

                RippleButton {
                    Layout.alignment: Qt.AlignTop
                    implicitWidth: 28
                    implicitHeight: 28
                    buttonRadius: Appearance.rounding.full
                    colBackground: root.blendedColors.colSecondaryContainer
                    colBackgroundHover: root.blendedColors.colSecondaryContainerHover
                    colRipple: root.blendedColors.colSecondaryContainerActive
                    releaseAction: () => root.toggleLyrics()

                    contentItem: MaterialSymbol {
                        text: "arrow_back"
                        iconSize: Appearance.font.pixelSize.large
                        color: root.blendedColors.colOnSecondaryContainer
                        horizontalAlignment: Text.AlignHCenter
                    }
                }
            }

            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumHeight: 0
                clip: true

                Lyrics {
                    id: lyricsComp
                    anchors.fill: parent
                    implicitHeight: 0
                    compact: true
                    firstSlot: Math.max(0, LyricsService.before - 1)
                    slotCount: 3
                    textColor: root.blendedColors.colOnLayer0
                    activeColor: root.blendedColors.colPrimary
                    dimColor: root.blendedColors.colSubtext
                    indicatorColor: {
                        const color = root.blendedColors.colPrimaryContainer
                        return color && color !== "#000000" && color !== "transparent"
                            ? color : root.artDominantColor
                    }
                    indicatorShapeColor: {
                        const color = root.blendedColors.colOnPrimaryContainer
                        if (color && color !== "#000000" && color !== "#ffffff"
                                && color !== "transparent")
                            return color
                        return root.blendedColors.colPrimary || Appearance.colors.colPrimary
                    }
                }
            }

            StyledText {
                Layout.fillWidth: true
                font.pixelSize: Appearance.font.pixelSize.small
                color: root.blendedColors.colSubtext
                font.features: { "tnum": 1 }
                text: `${StringUtils.friendlyTimeForSeconds(root.playbackPosition)} / `
                    + (root.playbackLengthKnown
                        ? StringUtils.friendlyTimeForSeconds(root.playbackLength) : "--:--")
            }
        }
    }
}
