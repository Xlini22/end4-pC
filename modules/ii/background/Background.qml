pragma ComponentBehavior: Bound

import qs
import qs.services
import qs.modules.common
import qs.modules.common.widgets
import qs.modules.common.widgets.widgetCanvas
import qs.modules.common.functions as CF
import QtQuick
import QtQuick.Layouts
import Qt5Compat.GraphicalEffects
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Hyprland

Variants {
    id: root
    model: Quickshell.screens

    PanelWindow {
        id: bgRoot

        required property var modelData
        property string currentWallpaperSource: Config.options.background.wallpaperPath
        property string previousWallpaperSource: Config.options.background.wallpaperPath
        property bool videoRevealed: false

        readonly property real splitFraction: {
            switch (Config.options.background.splitRatio) {
                case "25": return 0.28
                case "50": return 0.54
                default:   return 1.0
            }
        }
        readonly property bool overviewBlurActive: Config.options.overview.style === "niri" && GlobalStates.overviewOpen && Config.options.overview.enable
        readonly property bool userBlurActive: Config.options.background.showBlur && !bgRoot.wallpaperIsVideo
        readonly property bool blurFullScreen: bgRoot.overviewBlurActive || bgRoot.splitFraction >= 1.0

        property var shaderList: ["circlePit", "circleSelect", "magic", "Doom", "Peel", "transition", "pixelate", "stripes", "crt", "dissolve", "glitch", "ripple", "shatter"]
        property string currentShader: "pixelate"
        property string wallpaperAnimation: Config.options.background.wallpaperAnimation ?? "random"

        property list<HyprlandWorkspace> workspacesForMonitor: Hyprland.workspaces.values.filter(workspace => workspace.monitor && workspace.monitor.name == monitor.name)
        property var activeWorkspaceWithFullscreen: workspacesForMonitor.filter(workspace => ((workspace.toplevels.values.filter(window => window.wayland?.fullscreen)[0] != undefined) && workspace.active))[0]
        visible: true

        readonly property bool hiddenForFullscreen: !GlobalStates.screenLocked
            && (activeWorkspaceWithFullscreen != undefined)
            && Config?.options.background.hideWhenFullscreen

        property HyprlandMonitor monitor: Hyprland.monitorFor(modelData)

        // Workspace range and image geometry follow the original ii parallax.
        property list<var> relevantWindows: HyprlandData.windowList.filter(win => win.monitor == monitor?.id && win.workspace.id >= 0).sort((a, b) => a.workspace.id - b.workspace.id)
        readonly property int lastWorkspaceId: relevantWindows[relevantWindows.length - 1]?.workspace.id || 10
        readonly property int workspaceChunkSize: Math.max(1, Config.options.bar.workspaces.shown ?? 10)
        readonly property int totalWorkspaces: Math.ceil(lastWorkspaceId / workspaceChunkSize) * workspaceChunkSize
        // Centered wallpaper and video rendering are specific to this fork.
        readonly property bool parallaxAvailable: WM.compositor === "hyprland"
            && !wallpaperIsVideo && !centeredWallpaper.centeredWallpaperEnabled
        readonly property real parallaxRatio: parallaxAvailable
            ? Math.max(1, Config.options.background.parallax.workspaceZoom) : 1
        property real wallpaperWidth: modelData.width
        property real wallpaperHeight: modelData.height
        readonly property real minSuitableScale: Math.max(modelData.width / wallpaperWidth, modelData.height / wallpaperHeight)
        readonly property real scaledWallpaperWidth: wallpaperWidth * minSuitableScale * parallaxRatio
        readonly property real scaledWallpaperHeight: wallpaperHeight * minSuitableScale * parallaxRatio
        readonly property real parallaxTotalPixelsX: Math.max(0, scaledWallpaperWidth - modelData.width)
        readonly property real parallaxTotalPixelsY: Math.max(0, scaledWallpaperHeight - modelData.height)
        readonly property bool verticalParallax: Config.options.background.parallax.vertical
            || (Config.options.background.parallax.autoVertical && wallpaperHeight > wallpaperWidth)

        function updateZoomScale() {
            if (getWallpaperSizeProc.running) return;
            getWallpaperSizeProc.path = bgRoot.wallpaperPath;
            if (getWallpaperSizeProc.path) getWallpaperSizeProc.running = true;
        }
        Process {
            id: getWallpaperSizeProc
            property string path: ""
            command: ["magick", "identify", "-format", "%w %h", CF.FileUtils.trimFileProtocol(path) + "[0]"]
            stdout: StdioCollector {
                onStreamFinished: {
                    if (getWallpaperSizeProc.path !== bgRoot.wallpaperPath) return;
                    const dimensions = text.trim().split(/\s+/).map(Number);
                    if (dimensions.length !== 2 || !dimensions.every(n => Number.isFinite(n) && n > 0)) return;
                    bgRoot.wallpaperWidth = dimensions[0];
                    bgRoot.wallpaperHeight = dimensions[1];
                }
            }
            onExited: {
                // A preview can change while identify is still reading the previous image.
                if (path !== bgRoot.wallpaperPath) Qt.callLater(bgRoot.updateZoomScale);
            }
        }

        property string effectiveWallpaperPath: {
            if (GlobalStates.screenLocked && Config.options.background.lockWall !== "")
                return Config.options.background.lockWall;
            return Wallpapers.previewPath || Wallpapers.confirmedPath || Config.options.background.wallpaperPath;
        }

        property bool wallpaperIsVideo: bgRoot.effectiveWallpaperPath.endsWith(".mp4") || bgRoot.effectiveWallpaperPath.endsWith(".webm") || bgRoot.effectiveWallpaperPath.endsWith(".mkv") || bgRoot.effectiveWallpaperPath.endsWith(".avi") || bgRoot.effectiveWallpaperPath.endsWith(".mov")
        property string wallpaperPath: wallpaperIsVideo ? Config.options.background.thumbnailPath : bgRoot.effectiveWallpaperPath
        property bool wallpaperSafetyTriggered: {
            const enabled = Config.options.workSafety.enable.wallpaper;
            const sensitiveWallpaper = (CF.StringUtils.stringListContainsSubstring(wallpaperPath.toLowerCase(), Config.options.workSafety.triggerCondition.fileKeywords));
            const sensitiveNetwork = (CF.StringUtils.stringListContainsSubstring(Network.networkName.toLowerCase(), Config.options.workSafety.triggerCondition.networkNameKeywords));
            return enabled && sensitiveWallpaper && sensitiveNetwork;
        }

        property bool shouldBlur: (GlobalStates.screenLocked && Config.options.lock.blur.enable)
        property color dominantColor: Appearance.colors.colPrimary
        property bool dominantColorIsDark: dominantColor.hslLightness < 0.5
        property color colText: {
            if (wallpaperSafetyTriggered)
                return CF.ColorUtils.mix(Appearance.colors.colOnLayer0, Appearance.colors.colPrimary, 0.75);
            return (GlobalStates.screenLocked && shouldBlur) ? Appearance.colors.colOnLayer0 : CF.ColorUtils.colorWithLightness(Appearance.colors.colPrimary, (dominantColorIsDark ? 0.8 : 0.12));
        }
        Behavior on colText {
            animation: Appearance.animation.elementMoveFast.colorAnimation.createObject(this)
        }

        // Decode wallpapers at screen resolution. Uploading a 5K+ image and its mipmaps to the GPU
        // stalls the render thread, and the GUI thread with it while an animation is running.
        readonly property size wallpaperSourceSize: Qt.size(Math.ceil(modelData.width * modelData.devicePixelRatio),
            Math.ceil(modelData.height * modelData.devicePixelRatio))

        property real transitionProgress: 1.0
        property bool transitionPending: false

        screen: modelData
        exclusionMode: ExclusionMode.Ignore
        WlrLayershell.layer: (GlobalStates.screenLocked && !scaleAnim.running) ? WlrLayer.Overlay : WlrLayer.Bottom
        WlrLayershell.namespace: "quickshell:background"
        WlrLayershell.keyboardFocus: GlobalStates.desktopWidgetKeyboardFocus
            ? WlrKeyboardFocus.OnDemand
            : WlrKeyboardFocus.None
        anchors {
            top: true
            bottom: true
            left: true
            right: true
        }
        color: {
            if (!bgRoot.wallpaperSafetyTriggered || bgRoot.wallpaperIsVideo)
                return "transparent";
            return CF.ColorUtils.mix(Appearance.colors.colLayer0, Appearance.colors.colPrimary, 0.75);
        }
        Behavior on color {
            animation: Appearance.animation.elementMoveFast.colorAnimation.createObject(this)
        }

        Component.onCompleted: {
            bgRoot.updateZoomScale();
            previousWallpaper.source = bgRoot.wallpaperSafetyTriggered ? "" : bgRoot.wallpaperPath
            wallpaper.source = bgRoot.wallpaperSafetyTriggered ? "" : bgRoot.wallpaperPath
            bgRoot.currentWallpaperSource = bgRoot.wallpaperPath
            bgRoot.previousWallpaperSource = ""
            bgRoot.transitionProgress = 1.0
            if (bgRoot.wallpaperAnimation !== "") {
                bgRoot.currentShader = bgRoot.wallpaperAnimation === "random"
                    ? bgRoot.shaderList[Math.floor(Math.random() * bgRoot.shaderList.length)]
                    : bgRoot.wallpaperAnimation
            }
            bgRoot.videoRevealed = bgRoot.wallpaperIsVideo
        }

        onWallpaperPathChanged: {
            bgRoot.updateZoomScale();
            bgRoot.videoRevealed = false
            if (wallpaperSafetyTriggered) {
                bgRoot.transitionPending = false
                previousWallpaper.source = ""
                wallpaper.source = ""
                bgRoot.transitionProgress = 1.0
                return
            }
            if (bgRoot.wallpaperAnimation === "" || GlobalStates.startupLockPending) {
                bgRoot.transitionPending = false
                wallpaper.source = wallpaperPath
                previousWallpaper.source = wallpaperPath
                bgRoot.currentWallpaperSource = wallpaperPath
                if (!bgRoot.wallpaperIsVideo) return
                bgRoot.videoRevealed = true
                return
            }

            previousWallpaper.source = bgRoot.currentWallpaperSource
            bgRoot.currentWallpaperSource = wallpaperPath
            if (bgRoot.wallpaperAnimation === "random") {
                bgRoot.currentShader = bgRoot.shaderList[Math.floor(Math.random() * bgRoot.shaderList.length)]
            } else {
                bgRoot.currentShader = bgRoot.wallpaperAnimation
            }
            bgRoot.transitionPending = true
            wallpaper.source = wallpaperPath
            if (wallpaper.status === Image.Ready) {
                bgRoot.transitionPending = false
                bgRoot.transitionProgress = 0.0
                transitionAnim.restart()
            }
        }

        NumberAnimation {
            id: transitionAnim
            target: bgRoot
            property: "transitionProgress"
            from: 0.0
            to: 1.0
            duration: 1000
            easing.type: Easing.InOutQuad
            onFinished: {
                previousWallpaper.source = bgRoot.currentWallpaperSource
                bgRoot.previousWallpaperSource = ""
                bgRoot.transitionProgress = 1.0
                bgRoot.videoRevealed = bgRoot.wallpaperIsVideo
            }
        }

        Timer {
            id: wallpaperChangeTimer
            interval: Config.options.wallpaperSelector.changeInterval
            running: Config.options.wallpaperSelector.changeInterval > 0
            repeat: true
            onTriggered: {
                if (Wallpapers.folderModel.count > 0) {
                    Wallpapers.randomFromCurrentFolder()
                }
            }
        }

        Connections {
            target: Config
            function onReadyChanged() {
                if (!Config.ready) return
                bgRoot.setCenteredProgress(GlobalStates.screenLocked ? 0 : (bgRoot.centeredOnlyWhenLocked ? 1 : 0))
                bgRoot.centeredAnimationReady = true
            }
        }

        Connections {
            target: GlobalStates
            function onScreenLockedChanged() {
                if (!GlobalStates.screenLocked) {
                    bgRoot.videoRevealed = bgRoot.wallpaperIsVideo
                }
            }
        }

        Item {
            anchors.fill: parent
            opacity: (bgRoot.hiddenForFullscreen || GlobalStates.startupLockPending) ? 0 : 1
            enabled: !bgRoot.hiddenForFullscreen

            Behavior on opacity {
                NumberAnimation { duration: 150; easing.type: Easing.OutCubic }
            }

            // Move the wallpaper and its transition/blur layers together. Widgets
            // follow below with the original ii depth factor.
            Item {
                id: parallaxSurface
                width: bgRoot.parallaxAvailable ? bgRoot.scaledWallpaperWidth : parent.width
                height: bgRoot.parallaxAvailable ? bgRoot.scaledWallpaperHeight : parent.height
                readonly property int workspaceIndex: (bgRoot.monitor?.activeWorkspace?.id ?? 1) - 1
                readonly property real fraction: bgRoot.totalWorkspaces <= 1 ? 0.5
                    : Math.max(0, Math.min(1, workspaceIndex / (bgRoot.totalWorkspaces - 1)))
                readonly property real usedFractionX: {
                    let fractionX = Config.options.background.parallax.enableWorkspace && !bgRoot.verticalParallax ? fraction : 0.5;
                    if (Config.options.background.parallax.enableSidebar) {
                        const sidebarFraction = bgRoot.parallaxRatio / bgRoot.workspaceChunkSize / 2;
                        fractionX += sidebarFraction * (Number(GlobalStates.sidebarRightOpen) - Number(GlobalStates.sidebarLeftOpen));
                    }
                    return Math.max(0, Math.min(1, fractionX));
                }
                readonly property real usedFractionY: Config.options.background.parallax.enableWorkspace && bgRoot.verticalParallax ? fraction : 0.5
                x: bgRoot.parallaxAvailable ? -bgRoot.parallaxTotalPixelsX * usedFractionX : 0
                y: bgRoot.parallaxAvailable ? -bgRoot.parallaxTotalPixelsY * usedFractionY : 0
                Behavior on x {
                    NumberAnimation { duration: 600; easing.type: Easing.OutCubic }
                }
                Behavior on y {
                    NumberAnimation { duration: 600; easing.type: Easing.OutCubic }
                }

                Image {
                    id: previousWallpaper
                    anchors.fill: parent
                    fillMode: Image.PreserveAspectCrop
                    // Same size as `wallpaper` so this synchronous Image reuses its cached pixmap
                    sourceSize: bgRoot.wallpaperSourceSize
                    cache: true
                    mipmap: true
                    smooth: true
                    layer.enabled: true
                    visible: !bgRoot.videoRevealed
                    opacity: bgRoot.videoRevealed ? 0 : 1
                }

                StyledImage {
                    id: wallpaper
                    anchors.fill: parent
                    fillMode: Image.PreserveAspectCrop
                    sourceSize: bgRoot.wallpaperSourceSize
                    cache: true
                    smooth: true
                    mipmap: true
                    asynchronous: true
                    layer.enabled: bgRoot.wallpaperIsVideo ? false : true
                    visible: !blurLoader.active && !bgRoot.videoRevealed
                        && (bgRoot.wallpaperAnimation === "" || bgRoot.transitionProgress >= 1.0)
                        && !centeredWallpaper.centeredHidesFullWallpaper
                    opacity: centeredWallpaper.centeredFullWallpaperOpacity()
                    onStatusChanged: {
                        if (status === Image.Ready && bgRoot.transitionPending) {
                            bgRoot.transitionPending = false
                            bgRoot.transitionProgress = 0.0
                            transitionAnim.restart()
                        }
                    }
                }

                ShaderEffect {
                    id: transitionEffect
                    anchors.fill: parent
                    visible: !blurLoader.active && bgRoot.wallpaperAnimation !== "" && !centeredWallpaper.centeredShapeActive && !bgRoot.videoRevealed
                        && bgRoot.transitionProgress < 1.0

                    property var fromImage: previousWallpaper
                    property var toImage: wallpaper
                    property var source1: previousWallpaper
                    property var source2: wallpaper
                    property real time: 0.0
                    property real progress: bgRoot.transitionProgress
                    property real aspectX: width / height
                    property real aspectY: 1.0
                    property vector2d aspectRatio: Qt.vector2d(aspectX, aspectY)
                    property vector2d origin: Qt.vector2d(0.5, 0.5)

                    fragmentShader: bgRoot.wallpaperAnimation !== ""
                        ? Qt.resolvedUrl(`shaders/${bgRoot.currentShader}.frag.qsb`)
                        : ""

                    Timer {
                        interval: 16
                        repeat: true
                        running: transitionEffect.visible
                        onTriggered: transitionEffect.time += interval / 1000.0
                    }
                    onVisibleChanged: if (!visible) transitionEffect.time = 0.0
                }

                Loader {
                    id: blurLoader
                    // The blur is invisible while the centered wallpaper is active
                    // (opaque shape + solid background cover it), so skip it to
                    // save the expensive multi-sample blur pass on lock/unlock.
                    active: Config.options.lock.blur.enable && !centeredWallpaper.centeredWallpaperEnabled
                        && (GlobalStates.screenLocked || scaleAnim.running)
                        && !(bgRoot.userBlurActive || bgRoot.overviewBlurActive)
                    anchors.fill: parent
                    scale: GlobalStates.screenLocked ? Config.options.lock.blur.extraZoom : 1
                    Behavior on scale {
                        NumberAnimation {
                            id: scaleAnim
                            duration: 400
                            easing.type: Easing.BezierSpline
                            easing.bezierCurve: Appearance.animationCurves.expressiveDefaultSpatial
                        }
                    }
                    sourceComponent: GaussianBlur {
                        source: bgRoot.wallpaperAnimation === "" || bgRoot.transitionProgress >= 1.0 ? wallpaper : transitionEffect
                        radius: GlobalStates.screenLocked ? Config.options.lock.blur.radius : 0
                        samples: Config.options.lock.blur.size
                        Rectangle {
                            opacity: GlobalStates.screenLocked ? 1 : 0
                            anchors.fill: parent
                            color: CF.ColorUtils.transparentize(Appearance.colors.colLayer0, 0.7)
                        }
                    }
                }

                Loader {
                    id: fastBlurLoader
                    active: (bgRoot.userBlurActive || bgRoot.overviewBlurActive)
                        && (!GlobalStates.screenLocked || !centeredWallpaper.centeredWallpaperEnabled || bgRoot.blurFullScreen)
                    anchors.fill: parent

                    sourceComponent: Item {
                        id: blurRoot
                        anchors.fill: parent

                        readonly property real fadeWidth: 140
                        readonly property real blurRadius: 48
                        readonly property bool alignRight: Config.options.background.splitSide === "right"
                        property real coreWidth: bgRoot.blurFullScreen ? blurRoot.width : blurRoot.width * bgRoot.splitFraction

                        Behavior on coreWidth {
                            NumberAnimation { duration: 250; easing.type: Easing.OutCubic }
                        }

                        FastBlur {
                            id: blurLayer
                            anchors.fill: parent
                            source: bgRoot.wallpaperAnimation === "" || bgRoot.transitionProgress >= 1.0 ? wallpaper : transitionEffect
                            radius: Config.options.background.blurRadius

                            layer.enabled: !bgRoot.blurFullScreen
                            layer.effect: OpacityMask {
                                maskSource: Rectangle {
                                    width: blurLayer.width
                                    height: blurLayer.height
                                    gradient: Gradient {
                                        orientation: Gradient.Horizontal
                                        GradientStop { position: blurRoot.alignRight ? 1 - (blurRoot.coreWidth / blurRoot.width) : Math.max(0, (blurRoot.coreWidth - blurRoot.fadeWidth) / blurRoot.width); color: blurRoot.alignRight ? "transparent" : "white" }
                                        GradientStop { position: blurRoot.alignRight ? Math.min(1, 1 - (blurRoot.coreWidth - blurRoot.fadeWidth) / blurRoot.width) : Math.min(1, blurRoot.coreWidth / blurRoot.width); color: blurRoot.alignRight ? "white" : "transparent" }
                                    }
                                }
                            }
                        }
                    }
                }

            } // parallaxSurface

            /* Centered Wallpaper */
            CenteredWallpaper {
                id: centeredWallpaper
                anchors.fill: parent
                screen: bgRoot.screen
                wallpaperPath: bgRoot.wallpaperPath
                wallpaperIsVideo: bgRoot.wallpaperIsVideo
            }

            /* Wallpaper Drop Area */
            WallpaperDropArea {
                anchors.fill: parent
            }

            /* Widgets Loader */
            WidgetCanvas {
                id: widgetCanvas
                width: parent.width
                height: parent.height
                readonly property real parallaxFactor: Config.options.background.parallax.widgetsFactor / bgRoot.parallaxRatio
                readonly property real baseWallpaperOffsetX: (bgRoot.modelData.width - parallaxSurface.width) / 2
                readonly property real baseWallpaperOffsetY: (bgRoot.modelData.height - parallaxSurface.height) / 2
                x: bgRoot.parallaxAvailable && !GlobalStates.screenLocked
                    ? (parallaxSurface.x - baseWallpaperOffsetX) * parallaxFactor : 0
                y: bgRoot.parallaxAvailable && !GlobalStates.screenLocked
                    ? (parallaxSurface.y - baseWallpaperOffsetY) * parallaxFactor : 0

                transitions: Transition {
                    PropertyAnimation {
                        properties: "width,height"
                        duration: Appearance.animation.elementMove.duration
                        easing.type: Appearance.animation.elementMove.type
                        easing.bezierCurve: Appearance.animation.elementMove.bezierCurve
                    }
                    AnchorAnimation {
                        duration: Appearance.animation.elementMove.duration
                        easing.type: Appearance.animation.elementMove.type
                        easing.bezierCurve: Appearance.animation.elementMove.bezierCurve
                    }
                }

                MouseArea {
                    id: centeredDesktopThumpArea
                    width: Math.max(1, centeredWallpaper.centeredShapeSize())
                    height: width
                    anchors.centerIn: parent
                    visible: centeredWallpaper.centeredWallpaperEnabled
                        && !GlobalStates.screenLocked
                        && (centeredWallpaper.centeredProgress < 1 || centeredWallpaper.centeredAnimating)
                    acceptedButtons: Qt.LeftButton
                    onClicked: GlobalStates.centeredWallpaperThumpRequested()
                }

                WidgetsLoader {
                    screen: bgRoot.screen
                    wallpaperItem: wallpaper
                    wallpaperSafetyTriggered: bgRoot.wallpaperSafetyTriggered
                }
            }

            /* Desktop menu */
            MouseArea {
                id: desktopRightClickArea
                anchors.fill: parent
                z: -2
                acceptedButtons: Qt.RightButton
                onClicked: (mouse) => {
                    GlobalStates.desktopMenuScreen = bgRoot.screen
                    GlobalStates.desktopMenuX = mouse.x
                    GlobalStates.desktopMenuY = mouse.y
                    GlobalStates.desktopMenuOpen = true
                }
            }
        }
    }
}
