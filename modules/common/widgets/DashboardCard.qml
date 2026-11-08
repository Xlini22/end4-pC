import QtQuick
import qs.modules.common
import qs.modules.common.functions
import qs.services

Rectangle {
    id: root

    property color tint: Appearance.colors.colLayer1
    property real tintOpacity: 0.35
    property real cardRadius: Appearance.rounding.large
    property Item blurSource: null

    property Item pager: null
    property int animIndex: 0
    readonly property real speed: Math.max(0.5, Config.options.settings.animationSpeed ?? 1)
    property int staggerMs: 45
    property real travelX: 0
    property real travelY: 0

    property real animScale: 0.25
    property real animOpacity: 0
    property real offsetX: travelX
    property real offsetY: travelY

    readonly property bool glassDimmed: Config.options.background.widgets.glass.enable && Qt.colorEqual(tint, Appearance.colors.colLayer1)
    readonly property Item glassViewport: {
        for (let item = parent; item; item = item.parent)
            if (item.clip === true) return item
        return null
    }

    color: blurSource ? "transparent" : cardGlass.live ? ColorUtils.applyAlpha(tint, 0.72)
        : glassDimmed ? ColorUtils.applyAlpha(ColorUtils.mix(tint, "#000000", 0.5), 0.6) : tint
    radius: cardRadius

    WindowGlass {
        id: cardGlass
        anchors.fill: parent
        // Render the glass behind the card's coloured wash, including the wallpaper fallback.
        z: -1
        glassEnabled: !root.blurSource && GlassCompositor.windowFrostedAvailable
        cardRadius: root.cardRadius
        tint: root.tint
        frost: Math.max(8, Config.options.background.widgets.glass.haze)
        nativeClip: root.glassViewport
        trackGeometry: root.glassViewport?.dashboardSettingsViewport !== true
    }

    // The settings viewport tracks scrolling once; each tile only tracks its own animation and loader slot.
    readonly property var settingsGlassGeometry: cardGlass.enhancedNative && !cardGlass.trackGeometry
        ? [x, y, scale, opacity, offsetX, offsetY, parent?.x, parent?.y, parent?.scale, parent?.opacity] : []
    onSettingsGlassGeometryChanged: if (cardGlass.enhancedNative) GlassCompositor.queueRegions()

    transformOrigin: Item.Center
    scale: animScale
    opacity: animOpacity
    transform: Translate {
        x: root.offsetX
        y: root.offsetY
    }

    Loader {
        anchors.fill: parent
        anchors.margins: -1
        active: root.blurSource !== null

        sourceComponent: FastBlurred {
            blurSource: root.blurSource
            cardRadius: root.cardRadius + 1
            tint: root.tint
            tintOpacity: root.tintOpacity
            trackX: root.x + root.offsetX + root.animScale
            trackY: root.y + root.offsetY
        }
    }

    SequentialAnimation {
        id: enterAnim
        PauseAnimation { duration: root.animIndex * root.staggerMs }
        ParallelAnimation {
            SpringAnimation { target: root; property: "animScale"; to: 1; spring: 2.6 * root.speed; damping: 0.32 }
            SpringAnimation { target: root; property: "offsetX"; to: 0; spring: 2.6 * root.speed; damping: 0.32 }
            SpringAnimation { target: root; property: "offsetY"; to: 0; spring: 2.6 * root.speed; damping: 0.32 }
            NumberAnimation { target: root; property: "animOpacity"; to: 1; duration: 220 / root.speed; easing.type: Easing.OutQuad }
        }
    }

    SequentialAnimation {
        id: exitAnim
        PauseAnimation { duration: root.animIndex * (root.staggerMs - 4) }
        ParallelAnimation {
            NumberAnimation { target: root; property: "animScale"; to: 0.25; duration: 260 / root.speed; easing.type: Easing.InBack }
            NumberAnimation { target: root; property: "offsetX"; to: root.travelX; duration: 280 / root.speed; easing.type: Easing.InQuad }
            NumberAnimation { target: root; property: "offsetY"; to: root.travelY; duration: 280 / root.speed; easing.type: Easing.InQuad }
            NumberAnimation { target: root; property: "animOpacity"; to: 0; duration: 220 / root.speed; easing.type: Easing.InQuad }
        }
    }

    Component.onCompleted: enterAnim.start()

    Connections {
        target: root.pager
        ignoreUnknownSignals: true
        function onPageExitRequested() { enterAnim.stop(); exitAnim.restart() }
    }
}
