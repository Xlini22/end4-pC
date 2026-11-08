import QtQuick
import QtQuick.Layouts
import Quickshell
import qs
import qs.services
import qs.modules.common
import qs.modules.common.widgets

Scope {
    id: root

    readonly property bool active: GlobalStates.settingsOpen && Config.options.settings.style === "dashboard"

    Loader {
        active: root.active

        sourceComponent: FloatingWindow {
            id: window
            title: "illogical-impulse Settings"
            surfaceFormat.opaque: false // Glassy can become available after the window is created.
            color: GlassCompositor.active && GlassCompositor.windowFrostedAvailable ? "transparent" : Appearance.colors.colUiBackground

            WindowGlass {
                anchors.fill: parent
                glassEnabled: GlassCompositor.windowFrostedAvailable
                tint: Appearance.colors.colUiBackground
            }

            implicitWidth: 1100
            implicitHeight: 680
            minimumSize: Qt.size(900, 600)

            property bool settled: false

            visible: true
            onVisibleChanged: {
                if (!visible) GlobalStates.settingsOpen = false;
            }
            onWidthChanged: settleTimer.restart()
            onHeightChanged: settleTimer.restart()

            Timer {
                id: settleTimer
                interval: 70
                running: true
                onTriggered: window.settled = true
            }

            Loader {
                anchors.fill: parent
                active: window.settled

                sourceComponent: DashboardContent {}
            }
        }
    }
}
