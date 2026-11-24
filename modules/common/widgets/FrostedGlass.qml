import QtQuick
import "../functions/DarkeningWindow.js" as DarkeningWindow
import qs
import qs.services
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
    property real darkening: Number.isFinite(opticalProfile?.darkening) ? Math.max(0, Math.min(100, opticalProfile.darkening)) / 100 : 0
    property real automaticDarkeningStrength: GlassProfiles.darkeningStrength(opticalProfile)
    Behavior on automaticDarkeningStrength { NumberAnimation { duration: 800; easing.type: Easing.InOutQuad } }
    property bool automaticDarkeningVisible: true
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
        return { intervalMs: 1500, mode: "temporal-mean", automatic: root.automaticDarkening,
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
        active: root.automaticDarkening > 0
        sourceComponent: Item {
            id: state
            property var previousTexture: history
            property var targetTexture: history
            property var timeState: DarkeningWindow.create()
            property vector4d step: Qt.vector4d(0, 0, -1, -1)
            property real blend: 1
            property bool busy: false
            property bool initializing: true
            property bool restartPending: false
            readonly property bool samplingVisible: root.visible && root.automaticDarkeningVisible
            function visibilityChanged() {
                fade.stop();
                restartPending = true;
                if (samplingVisible) { initializing = true; sample(); }
            }
            Connections {
                target: root
                function onVisibleChanged() { state.visibilityChanged() }
                function onAutomaticDarkeningVisibleChanged() { state.visibilityChanged() }
            }

            function status() {
                return { busy, intervalMs: 1500, published: timeState.published, fading: fade.running, blend };
            }
            function sample() {
                if (busy || !samplingVisible) return;
                if (restartPending) {
                    timeState = DarkeningWindow.create();
                    restartPending = false;
                }
                const plan = DarkeningWindow.advance(timeState, Date.now() / 1000);
                if (plan[2] > 0) fade.pause();
                step = Qt.vector4d(plan[0], plan[1], plan[2], plan[2] < 0 ? -1 : blend);
                busy = true;
                history.scheduleUpdate();
            }
            Component.onCompleted: sample()
            Timer {
                interval: 100
                running: state.samplingVisible
                repeat: true
                onTriggered: state.sample()
            }
            NumberAnimation {
                id: fade
                target: state
                property: "blend"
                to: 1
                duration: 800
                easing.type: Easing.InOutQuad
            }
            ShaderEffect {
                id: probe
                blending: false
                width: 1; height: 1
                visible: false
                property var backdrop: capture
                property var historyLuma: history
                property real haze: root.haze
                property vector4d temporalStep: state.step
                vertexShader: Qt.resolvedUrl("shaders/glassLumaTemporal.vert.qsb")
                fragmentShader: Qt.resolvedUrl("shaders/glassLumaTemporal.frag.qsb")
            }
            ShaderEffectSource {
                id: history
                sourceItem: probe
                textureSize: Qt.size(1, 1)
                format: ShaderEffectSource.RGBA32F
                recursive: true
                live: false
                visible: false
                onScheduledUpdateCompleted: {
                    state.busy = false;
                    if (state.restartPending) { state.sample(); return; }
                    if (!state.samplingVisible) return;
                    if (state.step.z < 0) { state.blend = 1; state.initializing = false; }
                    if (state.step.z > 0) {
                        fade.stop();
                        state.blend = 0;
                        fade.start();
                    }
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
        property real holdDarkening: lumaState.item && !lumaState.item.initializing ? 1 : 0
        property real automaticDarkeningStrength: root.automaticDarkeningStrength
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
