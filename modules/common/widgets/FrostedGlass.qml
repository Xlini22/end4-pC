import QtQuick
import qs.modules.common

Item {
    id: root
    required property Item blurSource
    property bool hideSource: false
    property bool enhanced: Config.options.background.widgets.glass.enhanced
    property bool clearMaterial: false
    property real frost: 0
    property real cardRadius: 30
    property real topLeftRadius: cardRadius
    property real topRightRadius: cardRadius
    property real bottomRightRadius: cardRadius
    property real bottomLeftRadius: cardRadius
    property color tint: "white"
    property real tintOpacity: 0
    readonly property string tintChoice: Config.options.background.widgets.glass.tint ?? "transparent"
    readonly property bool tintOverride: tintChoice !== "transparent"
    readonly property color washColor: tintOverride ? Appearance.getColorFromName(tintChoice) : tint
    readonly property real washOpacity: enhanced ? 0 : tintOverride ? Config.options.background.widgets.glass.tintStrength : tintOpacity
    readonly property real rimWidth: enhanced ? Math.min(Math.min(width, height) * 0.07, 20) : Config.options.background.widgets.glass.rimWidth
    readonly property real pull: enhanced ? 1.35 * Math.min(rimWidth * 2.5, 80) : Config.options.background.widgets.glass.pull
    readonly property real split: Config.options.background.widgets.glass.split
    readonly property real haze: enhanced && clearMaterial && frost <= 0 ? 0 : Math.max(frost, Config.options.background.widgets.glass.haze)
    readonly property real vividness: enhanced ? 1 : Config.options.background.widgets.glass.vividness
    readonly property real sheen: Config.options.background.widgets.glass.sheen
    property real flareLeft: 0
    property real flareRight: 0
    property real hangLeft: 0
    property real hangRight: 0
    property int edge: 0
    property real trackX: 0
    property real trackY: 0
    property rect sourceRect: {
        var _fx = root.trackX
        var _fy = root.trackY
        if (!root.blurSource) return Qt.rect(0, 0, 0, 0)
        return root.mapToItem(root.blurSource, Qt.rect(0, 0, root.width, root.height))
    }

    ShaderEffectSource {
        id: capture
        sourceItem: root.blurSource
        sourceRect: root.sourceRect
        mipmap: true
        hideSource: root.hideSource
        live: true
        visible: false
    }

    ShaderEffect {
        anchors.fill: parent
        visible: root.blurSource !== null && root.width > 0 && root.height > 0

        property var backdrop: capture
        property vector2d size: Qt.vector2d(width, height)
        property vector4d radii: Qt.vector4d(root.topLeftRadius, root.topRightRadius, root.bottomRightRadius, root.bottomLeftRadius)
        property real rimWidth: root.rimWidth
        property real pull: root.pull
        property real split: root.split
        property real haze: root.haze
        property real vividness: root.vividness
        property real sheen: root.sheen
        property vector2d flares: Qt.vector2d(root.flareLeft, root.flareRight)
        property vector2d hangs: Qt.vector2d(root.hangLeft, root.hangRight)
        property real edge: root.edge
        property real enhanced: root.enhanced ? 1 : 0
        property real frosted: root.frost > 0 ? 1 : 0
        property color wash: Qt.rgba(root.washColor.r, root.washColor.g, root.washColor.b, root.washOpacity)

        fragmentShader: Qt.resolvedUrl("shaders/liquidLens.frag.qsb")
    }
}
