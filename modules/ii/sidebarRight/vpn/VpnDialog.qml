import QtQuick
import QtQuick.Layouts
import Quickshell
import qs
import qs.services
import qs.modules.common
import qs.modules.common.widgets

WindowDialog {
    id: root
    backgroundHeight: 600

    component VpnItem: DialogListItem {
        id: itemRoot
        required property var connection
        readonly property bool connected: Vpn.isActive(connection)
        width: ListView.view?.width ?? 0
        active: connected
        enabled: !Vpn.busy
        onClicked: connected ? Vpn.disconnect(connection) : Vpn.connect(connection)

        contentItem: RowLayout {
            anchors {
                fill: parent
                leftMargin: itemRoot.horizontalPadding
                rightMargin: itemRoot.horizontalPadding
                topMargin: itemRoot.verticalPadding
                bottomMargin: itemRoot.verticalPadding
            }
            spacing: 10

            MaterialSymbol {
                text: itemRoot.connected ? "enhanced_encryption" : "vpn_key"
                iconSize: Appearance.font.pixelSize.larger
                color: Appearance.colors.colOnSurfaceVariant
            }

            StyledText {
                Layout.fillWidth: true
                text: itemRoot.connection.name
                color: Appearance.colors.colOnSurfaceVariant
                elide: Text.ElideRight
                textFormat: Text.PlainText
            }

            MaterialSymbol {
                visible: itemRoot.connected
                text: "check"
                iconSize: Appearance.font.pixelSize.larger
                color: Appearance.colors.colOnSurfaceVariant
            }
        }
    }

    WindowDialogTitle {
        text: Translation.tr("VPN connections")
    }
    WindowDialogSeparator {}

    StyledText {
        Layout.fillWidth: true
        Layout.fillHeight: true
        visible: Vpn.connections.length === 0
        text: Translation.tr("No VPN profiles configured.")
        color: Appearance.colors.colSubtext
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        wrapMode: Text.Wrap
    }

    ListView {
        Layout.fillWidth: true
        Layout.fillHeight: true
        Layout.topMargin: -15
        Layout.bottomMargin: -16
        Layout.leftMargin: -Appearance.rounding.large
        Layout.rightMargin: -Appearance.rounding.large
        visible: Vpn.connections.length > 0
        clip: true
        spacing: 0
        model: ScriptModel { values: Vpn.connections }
        delegate: VpnItem {
            required property var modelData
            connection: modelData
        }
    }

    WindowDialogSeparator {}
    WindowDialogButtonRow {
        DialogButton {
            buttonText: Translation.tr("Details")
            onClicked: {
                root.dismiss()
                GlobalStates.sidebarRightOpen = false
                GlobalStates.settingsOpen = true
                Qt.callLater(() => GlobalStates.settingsPage = "Connectivity:VPN")
            }
        }
        Item { Layout.fillWidth: true }
        DialogButton {
            buttonText: Translation.tr("Done")
            onClicked: root.dismiss()
        }
    }

    onVisibleChanged: if (visible) Vpn.refresh()
}
