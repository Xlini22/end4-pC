pragma ComponentBehavior: Bound
import qs
import qs.modules.common
import qs.modules.common.models
import qs.modules.common.widgets
import qs.services
import qs.modules.common.functions
import Qt5Compat.GraphicalEffects
import QtQuick
import QtQuick.Effects
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import Quickshell.Services.Mpris

Item {
    id: root
    required property MprisPlayer player
    required property QtObject blendedColors
    required property string displayedArtFilePath
    required property real radius
    property bool useSharedTimeline: false
    property bool contentVisible: true
    property bool artInteractive: true
    readonly property real playbackPosition: useSharedTimeline
        ? MediaArtwork.playbackPosition : Number(player?.position ?? 0)
    readonly property real playbackLength: useSharedTimeline
        ? MediaArtwork.playbackLength : Number(player?.length ?? 0)
    readonly property bool playbackLengthKnown: useSharedTimeline
        ? MediaArtwork.durationKnown : playbackLength > 0
    signal toggleLyrics()

    function seekTo(position) {
        if (root.player)
            root.player.position = root.useSharedTimeline
                ? MediaArtwork.rawPositionFor(position) : position
    }

    component TrackChangeButton: RippleButton {
        id: trackChangeButton
        implicitWidth: 24
        implicitHeight: 24
        property var iconName
        property bool crossedOut: false
        colBackground: ColorUtils.transparentize(root.blendedColors.colSecondaryContainer, 1)
        colBackgroundHover: root.blendedColors.colSecondaryContainerHover
        colRipple: root.blendedColors.colSecondaryContainerActive
        contentItem: Item {
            MaterialSymbol {
                anchors.centerIn: parent
                iconSize: Appearance.font.pixelSize.huge
                fill: 1
                color: root.blendedColors.colOnSecondaryContainer
                text: trackChangeButton.iconName
                Behavior on color {
                    animation: Appearance.animation.elementMoveFast.colorAnimation.createObject(this)
                }
            }

            Rectangle {
                anchors.centerIn: parent
                width: 20
                height: 2
                radius: 1
                rotation: -45
                visible: trackChangeButton.crossedOut
                color: root.blendedColors.colOnSecondaryContainer
            }
        }
    }

    RowLayout {
        anchors.fill: parent
        anchors.margins: 13
        spacing: 15

        Rectangle {
            id: artBackground
            Layout.fillHeight: true
            implicitWidth: height
            radius: Appearance.rounding.verysmall
            color: ColorUtils.transparentize(root.blendedColors.colLayer1, 0.5)

            layer.enabled: true
            layer.effect: OpacityMask {
                maskSource: Rectangle {
                    width: artBackground.width
                    height: artBackground.height
                    radius: artBackground.radius + 6
                }
            }

            StyledImage {
                id: mediaArt
                property int size: parent.height
                anchors.fill: parent
                source: root.displayedArtFilePath
                fillMode: Image.PreserveAspectCrop
                cache: false
                antialiasing: true
                width: size
                height: size
                sourceSize.width: size
                sourceSize.height: size
            }

            HoverHandler {
                id: artHover
                enabled: root.artInteractive
            }

            Rectangle {
                anchors.fill: parent
                color: "black"
                opacity: root.artInteractive && artHover.hovered ? 0.6 : 0.0

                Behavior on opacity {
                    NumberAnimation {
                        duration: Appearance.animationCurves.expressiveFastSpatialDuration
                        easing.type: Easing.BezierSpline
                        easing.bezierCurve: Appearance.animationCurves.standard
                    }
                }
            }

            MaterialSymbol {
                anchors.centerIn: parent
                iconSize: Appearance.font.pixelSize.normal
                color: root.blendedColors.colOnLayer0
                text: (root.player?.volume ?? 0) === 0 ? "volume_off" : ((root.player?.volume ?? 0) < 0.5 ? "volume_down" : "volume_up")
                opacity: root.artInteractive && artHover.hovered ? 1.0 : 0.0

                Behavior on opacity {
                    NumberAnimation {
                        duration: Appearance.animationCurves.expressiveFastSpatialDuration
                        easing.type: Easing.BezierSpline
                        easing.bezierCurve: Appearance.animationCurves.standard
                    }
                }
            }

            MaterialDial {
                anchors.fill: parent
                anchors.margins: 14
                enabled: root.artInteractive
                colPrimary: root.blendedColors.colPrimary
                colSecondary: root.blendedColors.colSecondaryContainer
                value: root.player?.volume ?? 0
                waveAmplitude: 3.2 * (root.player?.volume ?? 0)
                opacity: root.artInteractive && artHover.hovered ? 1.0 : 0.0

                Behavior on opacity {
                    NumberAnimation {
                        duration: Appearance.animationCurves.expressiveFastSpatialDuration
                        easing.type: Easing.BezierSpline
                        easing.bezierCurve: Appearance.animationCurves.standard
                    }
                }

                onMoved: {
                    if (root.player)
                        root.player.volume = value;
                }
            }
        }

        ColumnLayout {
            Layout.fillHeight: true
            spacing: 2
            enabled: root.contentVisible
            opacity: root.contentVisible ? 1 : 0

            transform: Translate {
                x: root.contentVisible ? 0 : -28

                Behavior on x {
                    NumberAnimation { duration: 260; easing.type: Easing.OutCubic }
                }
            }

            Behavior on opacity {
                NumberAnimation { duration: 190; easing.type: Easing.OutCubic }
            }

            StyledText {
                id: trackTitle
                Layout.fillWidth: true
                font.pixelSize: Appearance.font.pixelSize.large
                color: root.blendedColors.colOnLayer0
                elide: Text.ElideRight
                text: StringUtils.cleanMusicTitle(root.player?.trackTitle) || "Untitled"
                animateChange: true
                animationDistanceX: 6
                animationDistanceY: 0
            }

            StyledText {
                id: trackArtist
                Layout.fillWidth: true
                font.pixelSize: Appearance.font.pixelSize.smaller
                color: root.blendedColors.colSubtext
                elide: Text.ElideRight
                text: root.player?.trackArtist
                animateChange: true
                animationDistanceX: 6
                animationDistanceY: 0
            }

            Item { Layout.fillHeight: true }

            Item {
                Layout.fillWidth: true
                implicitHeight: trackTime.implicitHeight + sliderRow.implicitHeight

                StyledText {
                    id: trackTime
                    anchors.bottom: sliderRow.top
                    anchors.bottomMargin: 5
                    anchors.left: parent.left
                    font.pixelSize: Appearance.font.pixelSize.small
                    color: root.blendedColors.colSubtext
                    elide: Text.ElideRight
                    font.features: { "tnum": 1 }
                    text: `${StringUtils.friendlyTimeForSeconds(root.playbackPosition)} / `
                        + (root.playbackLengthKnown
                            ? StringUtils.friendlyTimeForSeconds(root.playbackLength) : "--:--")
                }

                RowLayout {
                    id: sliderRow
                    anchors {
                        bottom: parent.bottom
                        left: parent.left
                        right: parent.right
                    }

                    TrackChangeButton {
                        iconName: "skip_previous"
                        downAction: () => root.player?.previous()
                    }

                    Item {
                        id: progressBarContainer
                        Layout.fillWidth: true
                        implicitHeight: Math.max(sliderLoader.implicitHeight, progressBarLoader.implicitHeight)

                        Loader {
                            id: sliderLoader
                            anchors.fill: parent
                            active: (root.player?.canSeek ?? false) && root.playbackLengthKnown
                            sourceComponent: StyledSlider {
                                configuration: StyledSlider.Configuration.Wavy
                                highlightColor: root.blendedColors.colPrimary
                                trackColor: root.blendedColors.colSecondaryContainer
                                handleColor: root.blendedColors.colPrimary
                                value: root.playbackLengthKnown
                                    ? root.playbackPosition / root.playbackLength : 0
                                onMoved: root.seekTo(value * root.playbackLength)
                            }
                        }

                        Loader {
                            id: progressBarLoader
                            anchors {
                                verticalCenter: parent.verticalCenter
                                left: parent.left
                                right: parent.right
                            }
                            active: !(root.player?.canSeek ?? false) || !root.playbackLengthKnown
                            sourceComponent: StyledProgressBar {
                                wavy: root.player?.isPlaying
                                highlightColor: root.blendedColors.colPrimary
                                trackColor: root.blendedColors.colSecondaryContainer
                                value: root.playbackLengthKnown
                                    ? root.playbackPosition / root.playbackLength : 0
                            }
                        }
                    }

                    TrackChangeButton {
                        iconName: "skip_next"
                        downAction: () => root.player?.next()
                    }

                    TrackChangeButton {
                        iconName: "lyrics"
                        visible: !GlobalStates.sidebarRightOpen
                        enabled: LyricsService.status !== "not_found"
                            && LyricsService.status !== "no_info"
                        crossedOut: !enabled
                        pointingHandCursor: enabled
                        releaseAction: () => root.toggleLyrics()
                    }

                    TrackChangeButton {
                        iconName: "equalizer"
                        downAction: () => GlobalStates.equalizerOpen = !GlobalStates.equalizerOpen
                    }
                }

                RippleButton {
                    id: playPauseButton
                    anchors.right: parent.right
                    anchors.bottom: sliderRow.top
                    anchors.bottomMargin: 5
                    property real size: 44
                    implicitWidth: size
                    implicitHeight: size
                    downAction: () => root.player.togglePlaying()

                    buttonRadius: root.player?.isPlaying ? Appearance?.rounding.normal : size / 2
                    colBackground: root.player?.isPlaying ? root.blendedColors.colPrimary : root.blendedColors.colSecondaryContainer
                    colBackgroundHover: root.player?.isPlaying ? root.blendedColors.colPrimaryHover : root.blendedColors.colSecondaryContainerHover
                    colRipple: root.player?.isPlaying ? root.blendedColors.colPrimaryActive : root.blendedColors.colSecondaryContainerActive

                    contentItem: MaterialSymbol {
                        iconSize: Appearance.font.pixelSize.huge
                        fill: 1
                        horizontalAlignment: Text.AlignHCenter
                        color: root.player?.isPlaying ? root.blendedColors.colOnPrimary : root.blendedColors.colOnSecondaryContainer
                        text: root.player?.isPlaying ? "pause" : "play_arrow"
                        Behavior on color {
                            animation: Appearance.animation.elementMoveFast.colorAnimation.createObject(this)
                        }
                    }
                }
            }
        }
    }
}
