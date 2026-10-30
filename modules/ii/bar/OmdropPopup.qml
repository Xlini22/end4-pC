pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Hyprland
import Quickshell.Wayland
import qs.modules.common
import qs.services
import qs.modules.common.widgets

PanelWindow {
    id: root
    objectName: "omdropPopup"
    required property var backend
    required property Item anchorTarget
    signal dismissed()
    readonly property bool barVertical: Config.options.bar.vertical
    readonly property bool barAtEnd: Config.options.bar.bottom
    readonly property real padding: Appearance.sizes.elevationMargin
    readonly property real barThickness: barVertical ? Appearance.sizes.verticalBarWidth : Appearance.sizes.barHeight
    readonly property point targetPosition: root.anchorTarget.QsWindow.window?.mapFromItem(root.anchorTarget, 0, 0) ?? Qt.point(0, 0)
    readonly property real offsetX: Math.max(0, Math.min(targetPosition.x + root.anchorTarget.width / 2 - width / 2, (screen?.width ?? width) - width))
    readonly property real offsetY: Math.max(0, Math.min(targetPosition.y + root.anchorTarget.height / 2 - height / 2, (screen?.height ?? height) - height))

    function syncName() {
        const name = root.backend.status.name ?? ""
        if (!nameField.edited || nameField.text === name) {
            nameField.text = name
            nameField.edited = false
        }
    }
    function saveName() {
        if (saveButton.enabled) root.backend.run(["name", nameField.text], Translation.tr("Saving…"))
    }

    visible: !root.backend.shuttingDown && root.backend.popupOpen
        && (root.anchorTarget.QsWindow.window?.visible ?? false)
    onVisibleChanged: if (visible) {
        root.syncName()
        Qt.callLater(() => { if (root?.visible) content.forceActiveFocus() })
    }
    screen: root.anchorTarget.QsWindow.window?.screen ?? null
    color: "transparent"
    implicitWidth: 360 + padding * 2
    implicitHeight: Math.min(content.implicitHeight + 16 + padding * 2, (screen?.height ?? 800) - barThickness - padding * 2)
    anchors.left: !root.barVertical || !root.barAtEnd
    anchors.right: root.barVertical && root.barAtEnd
    anchors.top: root.barVertical || !root.barAtEnd
    anchors.bottom: !root.barVertical && root.barAtEnd
    margins {
        left: root.barVertical ? (root.barAtEnd ? 0 : root.barThickness) : root.offsetX
        right: root.barVertical && root.barAtEnd ? root.barThickness : 0
        top: root.barVertical ? root.offsetY : (root.barAtEnd ? 0 : root.barThickness)
        bottom: !root.barVertical && root.barAtEnd ? root.barThickness : 0
    }
    exclusionMode: ExclusionMode.Ignore
    exclusiveZone: 0
    WlrLayershell.namespace: "quickshell:airdrop"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.OnDemand
    mask: Region { item: background }
    HyprlandFocusGrab {
        active: root.visible
        windows: [root]
        onCleared: root.dismissed()
    }
    Connections {
        target: root.backend
        function onStatusChanged() { root.syncName() }
    }
    StyledRectangularShadow { target: background }
    Rectangle {
        id: background
        anchors.fill: parent
        anchors.margins: root.padding
        radius: Appearance.rounding.normal + 4
        color: Appearance.colors.colLayer1Base
        border.width: 1
        border.color: Appearance.colors.colLayer0Border
        Flickable {
            id: scroll
            anchors.fill: parent
            anchors.margins: 8
            clip: true
            contentWidth: width
            contentHeight: content.implicitHeight
            boundsBehavior: Flickable.StopAtBounds
            ScrollBar.vertical: ScrollBar {}
            ColumnLayout {
                id: content
                width: scroll.width
                spacing: 8
                Keys.onEscapePressed: root.dismissed()
                RowLayout {
                    Layout.fillWidth: true
                    Layout.margins: 8
                    spacing: 8
                    Rectangle {
                        implicitWidth: 36
                        implicitHeight: 36
                        radius: Appearance.rounding.full
                        color: Appearance.colors.colPrimaryContainer
                        CustomIcon {
                            anchors.centerIn: parent
                            width: 22
                            height: 22
                            source: "airdrop-symbolic.svg"
                            colorize: true
                            color: Appearance.colors.colPrimary
                        }
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2
                        StyledText {
                            text: "AirDrop"
                            font.pixelSize: Appearance.font.pixelSize.normal
                            font.weight: Font.Medium
                            color: Appearance.colors.colOnSurfaceVariant
                        }
                        StyledText {
                            Layout.fillWidth: true
                            text: root.backend.stateText
                            color: Appearance.colors.colSubtext
                            font.pixelSize: Appearance.font.pixelSize.smaller
                            wrapMode: Text.WordWrap
                        }
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
                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: settings.implicitHeight + 24
                    radius: Appearance.rounding.normal
                    color: Appearance.colors.colSurfaceContainerLow
                    ColumnLayout {
                        id: settings
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 8
                        RowLayout {
                            Layout.fillWidth: true
                            visible: !root.backend.receiving
                            StyledText { Layout.fillWidth: true; text: Translation.tr("Stay visible for") }
                            StyledComboBox {
                                objectName: "omdropDuration"
                                Layout.fillWidth: false
                                Layout.preferredWidth: implicitWidth + 32
                                model: [Translation.tr("10 minutes"), Translation.tr("One file")]
                                currentIndex: root.backend.duration === "once" ? 1 : 0
                                enabled: !root.backend.busy
                                Accessible.name: Translation.tr("Stay visible for")
                                onActivated: index => root.backend.duration = index === 1 ? "once" : "10m"
                            }
                        }
                        StyledText { text: Translation.tr("They see you as"); font.pixelSize: Appearance.font.pixelSize.smaller; color: Appearance.colors.colOnSurfaceVariant }
                        RowLayout {
                            Layout.fillWidth: true
                            MaterialTextField {
                                id: nameField
                                objectName: "omdropNameField"
                                property bool edited: false
                                Layout.fillWidth: true
                                Layout.preferredHeight: 48
                                enabled: !root.backend.busy
                                maximumLength: 63
                                Accessible.name: Translation.tr("Computer name for AirDrop")
                                onTextEdited: edited = true
                                onAccepted: root.saveName()
                                Component.onCompleted: root.syncName()
                            }
                            DialogButton {
                                id: saveButton
                                objectName: "omdropSaveName"
                                buttonText: Translation.tr("Save")
                                enabled: !root.backend.busy && !!nameField.text.trim() && nameField.text !== root.backend.status.name
                                onClicked: root.saveName()
                            }
                        }
                        StyledText { text: Translation.tr("Save files to"); font.pixelSize: Appearance.font.pixelSize.smaller; color: Appearance.colors.colOnSurfaceVariant }
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
                    }
                }
                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: devices.implicitHeight + 24
                    radius: Appearance.rounding.normal
                    color: Appearance.colors.colSurfaceContainerLow
                    ColumnLayout {
                        id: devices
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 8
                        StyledPopupHeaderRow { icon: "devices"; label: Translation.tr("Nearby devices") }
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
                                MaterialSymbol { text: "phone_iphone"; iconSize: Appearance.font.pixelSize.large; color: Appearance.colors.colPrimary }
                                StyledText {
                                    Layout.fillWidth: true
                                    text: root.backend.peerNames[modelData.mac] || modelData.name || Translation.tr("Apple device")
                                    textFormat: Text.PlainText
                                    elide: Text.ElideRight
                                }
                                DialogButton {
                                    buttonText: Translation.tr("Send…")
                                    enabled: !root.backend.busy && root.backend.receiving
                                    onClicked: root.backend.run(["send", "--pick", "--to", modelData.mac], Translation.tr("Choose files…"))
                                }
                            }
                        }
                    }
                }
                StyledText {
                    Layout.fillWidth: true
                    Layout.margins: 8
                    text: Translation.tr("Depending on your Wi-Fi hardware, AirDrop may pause Wi-Fi until you turn it off.")
                    font.pixelSize: Appearance.font.pixelSize.smaller
                    color: Appearance.colors.colSubtext
                    wrapMode: Text.WordWrap
                }
                StyledText {
                    Layout.fillWidth: true
                    Layout.leftMargin: 8
                    Layout.rightMargin: 8
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
