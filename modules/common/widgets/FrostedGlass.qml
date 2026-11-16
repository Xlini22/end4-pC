import QtQuick
import qs
import qs.modules.common

Item {
    id: root
    required property Item blurSource
    property bool hideSource: false
    property bool enhanced: Config.options.background.widgets.glass.enhanced
    property bool clearMaterial: false
    property bool topBarOptics: false
    property var opticalProfile: null
    property real frost: 0
    property bool debounceDarkening: false
    property real darkening: Number.isFinite(opticalProfile?.darkening) ? Math.max(0, Math.min(100, opticalProfile.darkening)) / 100 : 0
    property real automaticDarkening: opticalProfile?.automaticDarkening ? 1 : 0
    Behavior on darkening { NumberAnimation { duration: 800; easing.type: Easing.InOutQuad } }
    Behavior on automaticDarkening { NumberAnimation { duration: 800; easing.type: Easing.InOutQuad } }
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
    readonly property real rimWidth: enhanced ? Math.min(Math.min(width, height) * (opticalProfile ? opticalProfile.rim / 100 : topBarOptics ? 0.24 : 0.07), 20) : Config.options.background.widgets.glass.rimWidth
    readonly property real pull: enhanced ? (opticalProfile ? opticalProfile.refraction / 100 : topBarOptics ? 2.0 : 1.35) * Math.min(rimWidth * 2.5, 80) : Config.options.background.widgets.glass.pull
    readonly property real split: Config.options.background.widgets.glass.split
    readonly property real haze: enhanced && opticalProfile && (clearMaterial || frost > 0 || GlobalStates.screenLocked) ? opticalProfile.blur : enhanced && topBarOptics ? 1 : enhanced && clearMaterial && frost <= 0 ? 0 : Math.max(frost, Config.options.background.widgets.glass.haze)
    readonly property real vividness: enhanced ? 1 : Config.options.background.widgets.glass.vividness
    readonly property real sheen: enhanced && opticalProfile ? opticalProfile.reflections / 100 : enhanced && topBarOptics ? 0.5 : Config.options.background.widgets.glass.sheen
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

    function darkeningStatus() {
        return { enabled: root.debounceDarkening, automatic: root.automaticDarkening,
            rect: [root.sourceRect.x, root.sourceRect.y, root.sourceRect.width, root.sourceRect.height],
            detail: lumaState.item?.status() ?? null }
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

    Loader {
        id: lumaState
        active: root.debounceDarkening && root.automaticDarkening > 0
        sourceComponent: Item {
            id: state
            property var previousTexture: previous
            property var targetTexture: target
            property real blend: 1
            property int motionSerial: 0
            property int sampleSerial: -1
            property bool busy: false

            function status() {
                return { motionSerial, sampleSerial, busy, waiting: settled.running,
                    fading: fade.running, blend, targetLive: target.live, previousLive: previous.live }
            }
            function moved() {
                motionSerial++
                fade.stop()
                settled.restart()
            }
            Connections {
                target: root
                function onSourceRectChanged() { state.moved() }
                function onHazeChanged() { state.moved() }
                function onBlurSourceChanged() { state.moved() }
            }
            Component.onCompleted: moved()
            Timer {
                id: settled
                interval: 1500
                repeat: false
                onTriggered: {
                    if (state.busy) { restart(); return }
                    state.busy = true
                    state.sampleSerial = state.motionSerial
                    previous.scheduleUpdate()
                }
            }
            NumberAnimation {
                id: fade
                target: state
                property: "blend"
                from: 0
                to: 1
                duration: 800
                easing.type: Easing.InOutQuad
            }
            ShaderEffect {
                id: probe
                width: 1; height: 1
                visible: false
                property var backdrop: capture
                property real haze: root.haze
                vertexShader: Qt.resolvedUrl("shaders/glassLuma.vert.qsb")
                fragmentShader: Qt.resolvedUrl("shaders/glassLuma.frag.qsb")
            }
            ShaderEffectSource {
                id: target
                sourceItem: probe
                textureSize: Qt.size(1, 1)
                // ponytail: only 1-pixel luma is held; the optical capture stays live.
                live: !settled.running && !state.busy && !fade.running
                visible: false
                onScheduledUpdateCompleted: {
                    if (!state.busy) return
                    state.busy = false
                    if (state.sampleSerial === state.motionSerial && !settled.running) fade.start()
                }
            }
            ShaderEffect {
                id: blended
                width: 1; height: 1
                visible: false
                property var previousLuma: previous
                property var targetLuma: target
                property real blend: state.blend
                fragmentShader: Qt.resolvedUrl("shaders/glassLumaBlend.frag.qsb")
            }
            ShaderEffectSource {
                id: previous
                sourceItem: blended
                textureSize: Qt.size(1, 1)
                recursive: true
                live: false
                visible: false
                onScheduledUpdateCompleted: {
                    state.blend = 0
                    if (state.sampleSerial === state.motionSerial && !settled.running) target.scheduleUpdate()
                    else state.busy = false
                }
            }
        }
    }

    ShaderEffect {
        anchors.fill: parent
        visible: root.blurSource !== null && root.width > 0 && root.height > 0

        property var backdrop: capture
        property var previousLuma: lumaState.item?.previousTexture ?? capture
        property var targetLuma: lumaState.item?.targetTexture ?? capture
        property real holdDarkening: lumaState.item ? 1 : 0
        property real darkeningBlend: lumaState.item?.blend ?? 1
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
        property real darkening: root.darkening
        property real automaticDarkening: root.automaticDarkening
        property color wash: Qt.rgba(root.washColor.r, root.washColor.g, root.washColor.b, root.washOpacity)

        vertexShader: Qt.resolvedUrl("shaders/liquidLens.vert.qsb")
        fragmentShader: Qt.resolvedUrl("shaders/liquidLens.frag.qsb")
    }
}
