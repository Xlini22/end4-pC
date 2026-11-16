import QtQuick
import Quickshell
import Quickshell.Wayland
import qs.services
import qs.modules.common
import qs.modules.common.widgets
import qs.modules.ii.bar as Bar

PanelWindow {
    id: root
    color: "transparent"
    implicitWidth: 180
    implicitHeight: 44
    readonly property var topBarWindow: GlobalFocusGrab.barWindows.find(window => window?.screen?.name === root.screen?.name) ?? null
    anchors.top: true
    margins.top: 5 + (root.topBarWindow?.visibleTopHeight ?? 0)
    exclusionMode: ExclusionMode.Ignore
    exclusiveZone: 0
    mask: Region {}
    // The detached volume pill shares the bar's optical profile in both renderers.
    WlrLayershell.namespace: "quickshell:bar"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.None

    Rectangle {
        id: pill
        anchors.fill: parent
        radius: height / 2
        color: volumeGlass.live ? "transparent" : Appearance.colors.colLayer0
        readonly property bool isMaterial: true
        function iconForProviderId(id) {
            return Audio.sink?.audio?.muted ? "volume_off" : "volume_up"
        }
        Accessible.role: Accessible.Indicator
        Accessible.name: Audio.sink?.audio?.muted ? Translation.tr("Muted")
            : Translation.tr("Volume") + " " + Math.round((Audio.sink?.audio?.volume ?? 0) * 100) + "%"

        WindowGlass {
            id: volumeGlass
            anchors.fill: parent
            glassEnabled: Config.options.background.widgets.glass.elements.bar.enable
            cardRadius: pill.radius
            tint: Appearance.colors.colLayer0
        }
        Bar.DiOsd {
            di: pill
            anchors.margins: 6
            anchors.leftMargin: 10
            anchors.rightMargin: 10
        }
    }
}
