import QtQuick
import QtQuick.Layouts
import Quickshell
import qs
import qs.services
import qs.modules.common
import qs.modules.common.widgets

WindowDialog {
    id: root
    backgroundHeight: 520

    component VpnItem: DialogListItem {
        id: itemRoot
        required property var connection
        readonly property bool connected: Vpn.isActive(connection)
        width: ListView.view?.width ?? 0
        active: connected
        pointingHandCursor: false

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

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 0

                StyledText {
                    Layout.fillWidth: true
                    text: itemRoot.connection.name
                    color: Appearance.colors.colOnSurfaceVariant
                    elide: Text.ElideRight
                    textFormat: Text.PlainText
                }

                StyledText {
                    Layout.fillWidth: true
                    text: itemRoot.connected ? Translation.tr("Connected") : Translation.tr("Not connected")
                    color: Appearance.colors.colSubtext
                    font.pixelSize: Appearance.font.pixelSize.smallie
                }
            }

            DialogButton {
                buttonText: itemRoot.connected ? Translation.tr("Disconnect") : Translation.tr("Connect")
                enabled: !Vpn.busy
                onClicked: itemRoot.connected ? Vpn.disconnect(itemRoot.connection) : Vpn.connect(itemRoot.connection)
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

    StyledListView {
        Layout.fillWidth: true
        Layout.fillHeight: true
        visible: Vpn.connections.length > 0
        clip: true
        spacing: 4
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
