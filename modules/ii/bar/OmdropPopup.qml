pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Hyprland
import qs.modules.common
import qs.services
import qs.modules.common.widgets

PopupWindow {
    id: root
    objectName: "omdropPopup"
    required property var backend
    required property Item anchorTarget
    signal dismissed()
    visible: !root.backend.shuttingDown && root.backend.popupOpen
        && (root.anchorTarget.QsWindow.window?.visible ?? false)
    onVisibleChanged: if (visible) Qt.callLater(() => { if (root?.visible) content.forceActiveFocus() })
    color: "transparent"
    implicitWidth: 360
    implicitHeight: Math.min(content.implicitHeight + 28, (root.anchorTarget.QsWindow.window?.screen?.height ?? 800) - 100)
    anchor {
        window: root.anchorTarget.QsWindow.window
        item: root.anchorTarget
        gravity: Config.options.bar.vertical
            ? (Config.options.bar.bottom ? Edges.Left : Edges.Right)
            : (Config.options.bar.bottom ? Edges.Top : Edges.Bottom)
        edges: Config.options.bar.vertical
            ? (Config.options.bar.bottom ? Edges.Left : Edges.Right)
            : (Config.options.bar.bottom ? Edges.Top : Edges.Bottom)
    }
    HyprlandFocusGrab {
        active: root.visible
        windows: [root]
        onCleared: root.dismissed()
    }
    Rectangle {
        anchors.fill: parent
        radius: Appearance.rounding.normal
        color: Appearance.colors.colLayer1Base
        border.width: 1
        border.color: Appearance.colors.colLayer0Border
        Flickable {
            id: scroll
            anchors.fill: parent
            anchors.margins: 14
            clip: true
            contentWidth: width
            contentHeight: content.implicitHeight
            boundsBehavior: Flickable.StopAtBounds
            ScrollBar.vertical: ScrollBar {}
            ColumnLayout {
                id: content
                width: scroll.width
                spacing: 12
                Keys.onEscapePressed: root.dismissed()
                RowLayout {
                    Layout.fillWidth: true
                    CustomIcon {
                        Layout.preferredWidth: 26
                        Layout.preferredHeight: 26
                        source: "airdrop-symbolic.svg"
                        colorize: true
                        color: Appearance.colors.colPrimary
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2
                        StyledText { text: "AirDrop"; font.pixelSize: Appearance.font.pixelSize.large; font.weight: Font.DemiBold }
                        StyledText { text: root.backend.stateText; color: Appearance.colors.colSubtext; font.pixelSize: Appearance.font.pixelSize.smaller }
                    }
                    StyledSwitch {
                        id: receiveToggle
                        enabled: root.backend.stateKnown && !root.backend.busy && (root.backend.receiving || root.backend.ready)
                        Accessible.name: Translation.tr("Receive with AirDrop")
                        onToggled: root.backend.run(checked ? ["on", "-e", root.backend.duration] : ["off"], checked ? Translation.tr("Starting…") : Translation.tr("Stopping…"))
                    }
                }
                Binding {
                    target: receiveToggle
                    property: "checked"
                    value: root.backend.receiving
                    when: !root.backend.busy
                    restoreMode: Binding.RestoreNone
                }
                StyledText {
                    Layout.fillWidth: true
                    text: Translation.tr("Depending on your Wi-Fi hardware, AirDrop may pause Wi-Fi until you turn it off.")
                    font.pixelSize: Appearance.font.pixelSize.smaller
                    color: Appearance.colors.colSubtext
                    wrapMode: Text.WordWrap
                }
                RowLayout {
                    Layout.fillWidth: true
                    visible: !root.backend.receiving
                    StyledText { Layout.fillWidth: true; text: Translation.tr("Stay visible for") }
                    StyledComboBox {
                        model: [Translation.tr("10 minutes"), Translation.tr("One file")]
                        currentIndex: root.backend.duration === "once" ? 1 : 0
                        enabled: !root.backend.busy && !root.backend.receiving
                        onActivated: index => root.backend.duration = index === 1 ? "once" : "10m"
                    }
                }
                StyledText { text: Translation.tr("They see you as"); font.pixelSize: Appearance.font.pixelSize.smaller; color: Appearance.colors.colSubtext }
                RowLayout {
                    Layout.fillWidth: true
                    MaterialTextField {
                        id: nameField
                        Layout.fillWidth: true
                        enabled: !root.backend.busy
                        maximumLength: 128
                        text: root.backend.status.name ?? ""
                        Accessible.name: Translation.tr("Computer name for AirDrop")
                    }
                    DialogButton {
                        buttonText: Translation.tr("Save")
                        enabled: !root.backend.busy && !!nameField.text.trim() && nameField.text !== root.backend.status.name
                        onClicked: root.backend.run(["name", nameField.text], Translation.tr("Saving…"))
                    }
                }
                Connections {
                    target: root.backend
                    function onStatusChanged() {
                        if (!nameField.activeFocus && !root.backend.busy) nameField.text = root.backend.status.name ?? ""
                    }
                }
                StyledText { text: Translation.tr("Save files to"); font.pixelSize: Appearance.font.pixelSize.smaller; color: Appearance.colors.colSubtext }
                RowLayout {
                    Layout.fillWidth: true
                    StyledText {
                        Layout.fillWidth: true
                        text: root.backend.status.dir
                        textFormat: Text.PlainText
                        elide: Text.ElideMiddle
                        font.pixelSize: Appearance.font.pixelSize.smaller
                    }
                    DialogButton {
                        buttonText: Translation.tr("Choose…")
                        enabled: !root.backend.busy
                        onClicked: root.backend.run(["dir", "--pick"], Translation.tr("Choose a folder…"))
                    }
                }
                Rectangle { Layout.fillWidth: true; implicitHeight: 1; color: Appearance.colors.colLayer0Border }
                StyledText { text: Translation.tr("Send to nearby devices"); font.weight: Font.Medium }
                StyledText {
                    Layout.fillWidth: true
                    visible: !root.backend.receiving || root.backend.peers.length === 0
                    text: !root.backend.receiving ? Translation.tr("Turn on AirDrop to find devices.")
                        : Translation.tr("Searching… On iPhone, choose Everyone for 10 minutes.")
                    color: Appearance.colors.colSubtext
                    font.pixelSize: Appearance.font.pixelSize.smaller
                    wrapMode: Text.WordWrap
                }
                Repeater {
                    model: root.backend.peers
                    delegate: RowLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2
                            StyledText {
                                Layout.fillWidth: true
                                text: root.backend.peerNames[modelData.mac] || modelData.name || Translation.tr("Apple device")
                                textFormat: Text.PlainText
                                elide: Text.ElideRight
                            }
                            StyledText { text: modelData.mac; color: Appearance.colors.colSubtext; font.pixelSize: Appearance.font.pixelSize.smallest }
                        }
                        DialogButton {
                            buttonText: Translation.tr("Send…")
                            enabled: !root.backend.busy && root.backend.receiving
                            onClicked: root.backend.run(["send", "--pick", "--to", modelData.mac], Translation.tr("Choose files…"))
                        }
                    }
                }
                StyledText {
                    Layout.fillWidth: true
                    visible: text.length > 0
                    text: root.backend.stateError || root.backend.prerequisite || root.backend.message || root.backend.status.reason || ""
                    textFormat: Text.PlainText
                    color: root.backend.failed || root.backend.stateError || root.backend.prerequisite ? Appearance.colors.colError : Appearance.colors.colSubtext
                    wrapMode: Text.WrapAnywhere
                    font.pixelSize: Appearance.font.pixelSize.smaller
                }
                DialogButton {
                    Layout.alignment: Qt.AlignRight
                    visible: root.backend.busy && root.backend.operation === "send"
                    buttonText: Translation.tr("Cancel")
                    onClicked: root.backend.cancel()
                }
            }
        }
    }
}
