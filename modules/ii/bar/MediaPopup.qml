import qs.modules.common
import qs.modules.common.widgets
import qs.services
import QtQuick
import QtQuick.Layouts
import Qt5Compat.GraphicalEffects
import Quickshell.Services.Mpris

StyledPopup {
    id: root

    readonly property MprisPlayer activePlayer: MprisController.activePlayer
    readonly property real trackLength: root.activePlayer?.length ?? 0
    readonly property bool hasKnownLength: root.trackLength > 0 && root.trackLength < 604800
    readonly property real progress: root.hasKnownLength
        ? Math.max(0, Math.min(1, (root.activePlayer?.position ?? 0) / root.trackLength)) : 0

    function formatTime(seconds) {
        if (!Number.isFinite(seconds) || seconds < 0) return "0:00"
        const total = Math.floor(seconds)
        const minutes = Math.floor(total / 60)
        return `${minutes}:${(total % 60).toString().padStart(2, "0")}`
    }

    ColumnLayout {
        implicitWidth: 300
        spacing: 10

        Timer {
            running: root.activePlayer?.playbackState === MprisPlaybackState.Playing
            interval: 1000
            repeat: true
            onTriggered: root.activePlayer?.positionChanged()
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            Rectangle {
                id: cover
                implicitWidth: 58
                implicitHeight: 58
                radius: Appearance.rounding.normal
                color: Appearance.colors.colPrimaryContainer
                clip: true

                layer.enabled: true
                layer.effect: OpacityMask {
                    maskSource: Rectangle {
                        width: cover.width
                        height: cover.height
                        radius: cover.radius
                    }
                }

                StyledImage {
                    anchors.fill: parent
                    source: root.activePlayer?.trackArtUrl ?? ""
                    fillMode: Image.PreserveAspectCrop
                    sourceSize.width: cover.width * 2
                    sourceSize.height: cover.height * 2
                    visible: (root.activePlayer?.trackArtUrl ?? "") !== ""
                }

                MaterialSymbol {
                    anchors.centerIn: parent
                    text: "music_note"
                    iconSize: 26
                    color: Appearance.colors.colPrimary
                    visible: (root.activePlayer?.trackArtUrl ?? "") === ""
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                Layout.preferredWidth: 222
                Layout.maximumWidth: 222
                spacing: 1

                StyledText {
                    Layout.fillWidth: true
                    text: root.activePlayer?.trackTitle || Translation.tr("No media")
                    font.pixelSize: Appearance.font.pixelSize.normal
                    font.weight: Font.DemiBold
                    color: Appearance.colors.colOnLayer1
                    elide: Text.ElideRight
                    maximumLineCount: 1
                }

                StyledText {
                    Layout.fillWidth: true
                    text: root.activePlayer?.trackArtist || Translation.tr("Unknown artist")
                    font.pixelSize: Appearance.font.pixelSize.smaller
                    color: Appearance.colors.colOnSurfaceVariant
                    opacity: 0.75
                    elide: Text.ElideRight
                    maximumLineCount: 1
                }

                RowLayout {
                    Layout.topMargin: 5
                    spacing: 5

                    MaterialSymbol {
                        text: root.activePlayer?.isPlaying ? "graphic_eq" : "pause"
                        iconSize: Appearance.font.pixelSize.small
                        color: Appearance.colors.colPrimary
                    }

                    StyledText {
                        text: root.activePlayer?.isPlaying
                            ? Translation.tr("Playing") : Translation.tr("Paused")
                        font.pixelSize: Appearance.font.pixelSize.smallest
                        color: Appearance.colors.colPrimary
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 4
            visible: root.hasKnownLength
            radius: 2
            color: Appearance.colors.colSurfaceContainerHigh

            Rectangle {
                width: parent.width * root.progress
                height: parent.height
                radius: parent.radius
                color: Appearance.colors.colPrimary

                Behavior on width {
                    NumberAnimation { duration: 180; easing.type: Easing.OutCubic }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            visible: root.hasKnownLength

            StyledText {
                text: root.formatTime(root.activePlayer?.position ?? 0)
                font.pixelSize: Appearance.font.pixelSize.smallest
                font.features: { "tnum": 1 }
                color: Appearance.colors.colOnSurfaceVariant
            }

            Item { Layout.fillWidth: true }

            StyledText {
                text: root.formatTime(root.trackLength)
                font.pixelSize: Appearance.font.pixelSize.smallest
                font.features: { "tnum": 1 }
                color: Appearance.colors.colOnSurfaceVariant
            }
        }
    }
}
