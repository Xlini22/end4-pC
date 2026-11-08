import qs.modules.common
import QtQuick
import qs.services

Text {
    id: root
    property bool animateChange: false
    property real animationDistanceX: 0
    property real animationDistanceY: 6

    renderType: Text.NativeRendering
    verticalAlignment: Text.AlignVCenter
    property bool shouldUseNumberFont: /^\d+$/.test(root.text)
    property var defaultFont: shouldUseNumberFont ? Appearance.font.family.numbers : Appearance.font.family.main
    
    font {
        hintingPreference: Font.PreferDefaultHinting
        family: defaultFont
        pixelSize: Appearance?.font.pixelSize.small ?? 15
        variableAxes: shouldUseNumberFont ? ({}) : Appearance.font.variableAxes.main
    }
    // Opt in only for labels painted directly on glass; filled controls keep their own ink.
    property bool adaptiveGlass: false
    property color baseColor: Appearance?.m3colors.m3onBackground ?? "black"
    property color glassInk: baseColor
    function updateGlassInk() {
        glassInk = adaptiveGlass ? GlassCompositor.foreground(root, baseColor, glassInk) : baseColor
    }
    onAdaptiveGlassChanged: updateGlassInk()
    onBaseColorChanged: updateGlassInk()
    onVisibleChanged: if (visible) updateGlassInk()
    color: adaptiveGlass ? glassInk : baseColor
    Connections {
        target: GlassCompositor
        enabled: root.adaptiveGlass && root.visible
        function onContrastTickChanged() { root.updateGlassInk() }
        function onContrastActiveChanged() { root.updateGlassInk() }
    }
    linkColor: Appearance?.m3colors.m3primary

    component Anim: NumberAnimation {
        target: root
        duration: 300 / 2
        easing.type: Easing.BezierSpline
        easing.bezierCurve: Appearance.animation.elementMoveFast.bezierCurve
    }

    Component.onCompleted: {
        root.updateGlassInk()
        textAnimationBehavior.originalX = root.x;
        textAnimationBehavior.originalY = root.y;
    }

    Behavior on text {
        id: textAnimationBehavior
        property real originalX: root.x
        property real originalY: root.y
        enabled: root.animateChange

        SequentialAnimation {
            alwaysRunToEnd: true
            ParallelAnimation {
                Anim {
                    property: "x"
                    to: textAnimationBehavior.originalX - root.animationDistanceX
                    easing.type: Easing.InSine
                }
                Anim {
                    property: "y"
                    to: textAnimationBehavior.originalY - root.animationDistanceY
                    easing.type: Easing.InSine
                }
                Anim {
                    property: "opacity"
                    to: 0
                    easing.type: Easing.InSine
                }
            }
            PropertyAction {} // Tie the text update to this point (we don't want it to happen during the first slide+fade)
            PropertyAction {
                target: root
                property: "x"
                value: textAnimationBehavior.originalX + root.animationDistanceX
            }
            PropertyAction {
                target: root
                property: "y"
                value: textAnimationBehavior.originalY + root.animationDistanceY
            }
            ParallelAnimation {
                Anim {
                    property: "x"
                    to: textAnimationBehavior.originalX
                    easing.type: Easing.OutSine
                }
                Anim {
                    property: "y"
                    to: textAnimationBehavior.originalY
                    easing.type: Easing.OutSine
                }
                Anim {
                    property: "opacity"
                    to: 1
                    easing.type: Easing.OutSine
                }
            }
        }
    }
}
