pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Dialogs as Dialogs
import QtQuick.Layouts
import qs.services
import qs.modules.common
import qs.modules.common.functions
import qs.modules.common.widgets

Item {
    id: root
    property var inputField: prompt
    property double now: Date.now()

    Timer {
        interval: 1000
        running: root.visible && Codex.authenticated
        repeat: true
        onTriggered: {
            const previous = root.now;
            root.now = Date.now();
            if ([Codex.fiveHourLimit, Codex.weeklyLimit].some(quota =>
                quota?.resetsAt * 1000 > previous && quota.resetsAt * 1000 <= root.now)) Codex.refreshLimits();
        }
    }

    component ActivitySpinner: MaterialLoadingIndicator {
        implicitSize: 16
        colBg: "transparent"
        colShape: Appearance.colors.colPrimary
        loading: visible
    }

    component AttachmentPreview: RowLayout {
        id: preview
        required property string filePath
        property int thumbnailSize: 64
        spacing: 8
        Rectangle {
            Layout.preferredWidth: preview.thumbnailSize
            Layout.preferredHeight: preview.thumbnailSize
            radius: Appearance.rounding.small
            color: Appearance.colors.colLayer3
            Image {
                id: thumbnail
                anchors.fill: parent
                anchors.margins: 2
                source: /\.(png|jpe?g|webp|gif)$/i.test(preview.filePath)
                    ? "file://" + preview.filePath.split("/").map(encodeURIComponent).join("/") : ""
                sourceSize: Qt.size(preview.thumbnailSize * 2, preview.thumbnailSize * 2)
                fillMode: Image.PreserveAspectFit
                asynchronous: true
                visible: status === Image.Ready
                Accessible.name: preview.filePath
            }
            MaterialSymbol {
                anchors.centerIn: parent
                visible: thumbnail.status !== Image.Ready
                text: thumbnail.status === Image.Error ? "broken_image" : "description"
                color: Appearance.colors.colSubtext
            }
        }
        StyledText {
            Layout.fillWidth: true
            text: preview.filePath.split("/").pop()
            textFormat: Text.PlainText
            elide: Text.ElideMiddle
            font.pixelSize: Appearance.font.pixelSize.small
            Accessible.name: preview.filePath
        }
    }

    Component.onCompleted: Codex.connect()
    Component.onDestruction: Codex.fileDialogOpen = false
    onFocusChanged: if (focus) prompt.forceActiveFocus()

    Dialogs.FileDialog {
        id: attachmentPicker
        title: qsTr("Allega file a Codex")
        fileMode: Dialogs.FileDialog.OpenFiles
        onVisibleChanged: Codex.fileDialogOpen = visible
        onAccepted: Codex.attachFiles(selectedFiles)
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.leftMargin: 16
        anchors.rightMargin: 16
        anchors.topMargin: 8
        anchors.bottomMargin: 12
        spacing: 8

        RowLayout {
            id: chatHeader
            Layout.fillWidth: true
            StyledText {
                id: chatTitle
                Layout.fillWidth: true
                Layout.minimumWidth: 0
                text: {
                    const thread = Codex.history.find(item => item.id === Codex.threadId);
                    return thread?.name || thread?.preview || (Codex.threadId ? qsTr("Chat Codex") : qsTr("Nuova chat"));
                }
                textFormat: Text.PlainText
                elide: Text.ElideRight
                maximumLineCount: 1
                font.weight: Font.Medium
                HoverHandler { id: titleHover }
                ToolTip.visible: titleHover.hovered
                ToolTip.text: chatTitle.text
            }
            DialogButton {
                id: settingsToggle
                Layout.alignment: Qt.AlignRight
                checkable: true
                buttonText: qsTr("Impostazioni") + (checked ? " ▴" : " ▾")
                Accessible.name: qsTr("Impostazioni")
            }
        }

        RowLayout {
            Layout.fillWidth: true
            visible: Codex.authenticated && Codex.account === "ChatGPT"
            spacing: 16
            Repeater {
                model: [
                    {label: qsTr("Settimana"), quota: Codex.weeklyLimit},
                    {label: qsTr("5 ore"), quota: Codex.fiveHourLimit}
                ]
                delegate: ColumnLayout {
                    id: usage
                    required property var modelData
                    Layout.fillWidth: true
                    Layout.preferredWidth: 1
                    spacing: 4
                    readonly property string resetText: Codex.rateLimitsError || (modelData.quota?.resetsAt > 0
                        ? qsTr("Reset: %1").arg(Qt.formatDateTime(new Date(modelData.quota.resetsAt * 1000), "dd/MM HH:mm"))
                        : qsTr("Consumo non disponibile"))
                    HoverHandler { id: usageHover }
                    ToolTip.visible: usageHover.hovered
                    ToolTip.text: resetText
                    StyledText {
                        Layout.fillWidth: true
                        text: usage.modelData.label + " · " + (usage.modelData.quota
                            ? qsTr("%1% rimanente").arg(Math.max(0, 100 - usage.modelData.quota.usedPercent)) : "—")
                        font.pixelSize: Appearance.font.pixelSize.smaller
                    }
                    ProgressBar {
                        id: usageBar
                        Layout.fillWidth: true
                        value: usage.modelData.quota ? Math.max(0, 100 - usage.modelData.quota.usedPercent) : 0
                        from: 0
                        to: 100
                        Accessible.name: usage.modelData.label
                        Accessible.description: usage.resetText
                        background: Rectangle {
                            implicitHeight: 4
                            radius: 2
                            color: Appearance.colors.colLayer3
                        }
                        contentItem: Item {
                            implicitHeight: 4
                            Rectangle {
                                width: parent.width * usageBar.visualPosition
                                height: parent.height
                                radius: 2
                                color: Appearance.colors.colPrimary
                            }
                        }
                    }
                    StyledText {
                        Layout.fillWidth: true
                        text: root.resetCountdown(usage.modelData.quota?.resetsAt, root.now)
                            + (usage.modelData.quota?.resetsAt > 0 && Number.isFinite(usage.modelData.quota.resetsAt)
                                ? " · " + Qt.formatDateTime(new Date(usage.modelData.quota.resetsAt * 1000), "HH:mm") : "")
                        font.pixelSize: Appearance.font.pixelSize.smaller
                        color: Appearance.colors.colSubtext
                        wrapMode: Text.Wrap
                    }
                }
            }
        }

        Popup {
            id: settingsPopup
            parent: settingsToggle
            x: settingsToggle.width - width
            y: settingsToggle.height + 8
            width: root.width - 32
            padding: 12
            visible: settingsToggle.checked
            focus: true
            closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent
            onClosed: settingsToggle.checked = false
            background: Rectangle {
                radius: Appearance.rounding.small
                color: ColorUtils.transparentize(Appearance.m3colors.m3surfaceContainer, 0.04)
                border.width: 1
                border.color: ColorUtils.transparentize(Appearance.m3colors.m3outlineVariant, 0.45)
            }
            contentItem: ColumnLayout {
                spacing: 8

                RowLayout {
                    Layout.fillWidth: true
                    StyledText {
                        Layout.fillWidth: true
                        text: !Codex.ready ? qsTr("Codex · disconnected") : !Codex.authenticated ? qsTr("Codex · sign in")
                            : Codex.busy ? qsTr("Codex · working") : "Codex · " + Codex.account
                        elide: Text.ElideRight
                    }
                    DialogButton {
                        buttonText: Codex.ready ? qsTr("Reconnect") : qsTr("Connect")
                        enabled: !Codex.busy
                        onClicked: Codex.reconnect()
                        ToolTip.visible: hovered
                        ToolTip.delay: 500
                        ToolTip.text: qsTr("Riavvia il collegamento a Codex CLI e tenta di riprendere l’ultima conversazione.")
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    MaterialTextField {
                        id: directory
                        Layout.fillWidth: true
                        enabled: !Codex.busy
                        text: Config.options.ai.codex.workspace
                        placeholderText: qsTr("Absolute project directory")
                        Accessible.name: qsTr("Project directory")
                        onEditingFinished: {
                            if (text.trim() !== Config.options.ai.codex.workspace) {
                                Codex.newConversation();
                                Config.options.ai.codex.workspace = text.trim();
                            }
                        }
                    }
                    DialogButton {
                        buttonText: qsTr("New")
                        enabled: !Codex.busy
                        onClicked: Codex.newConversation()
                    }
                }

                StyledComboBox {
                    Layout.fillWidth: true
                    enabled: Codex.ready && !Codex.busy
                    model: [{id: "", label: qsTr("Choose conversation")}].concat(Codex.history.map(item => ({
                        id: item.id, label: item.name || item.preview || item.id
                    })))
                    textRole: "label"
                    Accessible.name: qsTr("Conversation history")
                    onActivated: {
                        const id = model[currentIndex].id;
                        currentIndex = 0;
                        if (id) Codex.resume(id);
                    }
                }

                StyledText {
                    Layout.fillWidth: true
                    visible: !Config.options.ai.codex.allowEdits
                    text: qsTr("Read-only commands. Choose Edit project to allow changes.")
                    wrapMode: Text.Wrap
                    font.pixelSize: Appearance.font.pixelSize.smaller
                }
            }
        }

        DialogButton {
            Layout.fillWidth: true
            visible: Codex.ready && !Codex.authenticated
            enabled: !Codex.loginId
            buttonText: Codex.loginId ? qsTr("Complete sign-in in your browser…") : qsTr("Sign in with ChatGPT")
            onClicked: Codex.login()
        }

        StyledText {
            Layout.fillWidth: true
            visible: Codex.error.length > 0
            text: Codex.error
            textFormat: Text.PlainText
            wrapMode: Text.Wrap
            color: Appearance.colors.colError
        }
        DialogButton {
            visible: Codex.error.length > 0 && (Codex.lastPrompt.length > 0 || Codex.lastAttachments.length > 0) && !Codex.busy
            buttonText: qsTr("Restore last prompt")
            onClicked: {
                prompt.text = Codex.lastPrompt;
                Codex.attachments = Codex.lastAttachments.slice();
            }
        }

        ListView {
            id: conversation
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            spacing: 8
            model: Codex.messageGroups
            boundsBehavior: Flickable.StopAtBounds
            flickableDirection: Flickable.VerticalFlick
            flickDeceleration: 4000
            maximumFlickVelocity: 2500
            ScrollBar.vertical: StyledScrollBar {
                id: chatScrollBar
                onPressedChanged: conversation.followOutput = !pressed && conversation.atYEnd
            }
            property bool followOutput: true
            onMovementStarted: followOutput = false
            onMovementEnded: followOutput = atYEnd
            onContentHeightChanged: if (followOutput) Qt.callLater(conversation.followLatest)
            onHeightChanged: if (followOutput) Qt.callLater(conversation.followLatest)

            function followLatest() {
                if (followOutput && !moving && !chatTouchpad.scrolling && !chatWheel.active && !chatScrollBar.pressed)
                    positionViewAtEnd();
            }

            WheelHandler {
                id: chatWheel
                target: null
                blocking: false
                acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
                onWheel: event => {
                    if (event.angleDelta.y !== 0 || event.pixelDelta.y !== 0) conversation.followOutput = false;
                    event.accepted = false;
                }
                onActiveChanged: if (!active && !conversation.moving) conversation.followOutput = conversation.atYEnd
            }

            TouchpadScrollArea {
                id: chatTouchpad
                flickable: conversation
                visible: true
                touchpadScrollFactor: Config.options.interactions.scrolling.fasterTouchpadScroll
                    ? Config.options.interactions.scrolling.touchpadScrollFactor : 1
                touchpadSensitivity: Config.options.interactions.scrolling.fasterTouchpadScroll
                    ? Config.options.interactions.scrolling.touchpadSensitivity : 1
                onScrollingChanged: conversation.followOutput = !scrolling && conversation.atYEnd
            }

            delegate: Item {
                id: entry
                required property string kind
                required property int startIndex
                required property int itemCount
                required property int commandCount
                required property int fileCount
                readonly property bool hasLiveCommand: kind === "activity" && Codex.liveCommandIndex >= startIndex
                    && Codex.liveCommandIndex < startIndex + itemCount
                readonly property int historicalCommands: commandCount - (hasLiveCommand ? 1 : 0)
                readonly property var messageData: Codex.messages.get(startIndex)
                readonly property string title: messageData.title
                readonly property string text: messageData.text
                readonly property string status: messageData.status
                readonly property var files: JSON.parse(messageData.files)
                property bool expanded: kind === "agentMessage" || kind === "userMessage"
                width: conversation.width
                implicitHeight: bubble.implicitHeight
                readonly property bool isMessage: kind === "agentMessage" || kind === "userMessage"

                TextMetrics {
                    id: messageMetrics
                    font: message.font
                    text: entry.text
                }

                Rectangle {
                    id: bubble
                    x: entry.kind === "userMessage" ? entry.width - width : 0
                    width: entry.isMessage
                        ? Math.min(entry.width * 0.9, Math.max(entry.files.length ? 240 : 0,
                            Math.ceil(Math.max(messageMetrics.advanceWidth, messageMetrics.boundingRect.width)) + 25))
                        : entry.width
                    implicitHeight: body.implicitHeight + 24
                    radius: Appearance.rounding.small
                    color: entry.kind === "userMessage"
                        ? ColorUtils.transparentize(Appearance.colors.colPrimaryContainer, 0.12)
                        : entry.kind === "agentMessage"
                            ? Qt.hsla(0, 0, Appearance.m3colors.m3surfaceContainerHigh.hslLightness, 0.88)
                            : Appearance.colors.colLayer1
                    border.width: entry.kind === "userMessage" ? 1 : 0
                    border.color: ColorUtils.transparentize(Appearance.colors.colPrimary, 0.7)

                    ColumnLayout {
                        id: body
                        anchors { left: parent.left; right: parent.right; top: parent.top; margins: 12 }
                        spacing: 6
                        Button {
                            id: heading
                            Layout.fillWidth: true
                            visible: !entry.isMessage && (entry.kind !== "activity" || entry.historicalCommands > 0 || entry.fileCount > 0)
                            text: entry.kind === "activity"
                                ? [entry.historicalCommands ? (entry.historicalCommands === 1 ? qsTr("1 comando") : qsTr("%1 comandi").arg(entry.historicalCommands)) : "",
                                    entry.fileCount ? (entry.fileCount === 1 ? qsTr("1 file modificato") : qsTr("%1 file modificati").arg(entry.fileCount)) : ""
                                  ].filter(part => part).join(" · ") + (entry.expanded ? " ▴" : " ▾")
                                : entry.title + (entry.status ? " · " + entry.status : "")
                            background: Rectangle {
                                color: "transparent"
                                radius: Appearance.rounding.small
                                border.width: heading.visualFocus ? 1 : 0
                                border.color: Appearance.colors.colPrimary
                            }
                            contentItem: StyledText {
                                text: heading.text
                                textFormat: Text.PlainText
                                horizontalAlignment: Text.AlignLeft
                                verticalAlignment: Text.AlignVCenter
                                font.pixelSize: Appearance.font.pixelSize.small
                                color: Appearance.colors.colOnLayer1
                            }
                            Accessible.name: heading.text
                            onClicked: {
                                conversation.followOutput = false;
                                entry.expanded = !entry.expanded;
                            }
                        }
                        TextEdit {
                            id: message
                            Layout.fillWidth: true
                            visible: entry.expanded && entry.kind !== "activity" && entry.text.length > 0
                            text: entry.text
                            // ponytail: plain text avoids loading model-supplied images; rich output needs a sanitized renderer.
                            textFormat: TextEdit.PlainText
                            readOnly: true
                            selectByMouse: true
                            wrapMode: TextEdit.Wrap
                            font.family: ["commandExecution", "fileChange"].includes(entry.kind)
                                ? Appearance.font.family.monospace : Appearance.font.family.main
                            font.pixelSize: Appearance.font.pixelSize.small
                            color: entry.kind === "userMessage" ? Appearance.colors.colOnPrimaryContainer : Appearance.colors.colOnLayer1
                            onLinkActivated: link => {
                                if (/^https?:\/\//.test(link)) Qt.openUrlExternally(link);
                            }
                            Accessible.name: entry.title
                        }
                        Repeater {
                            model: entry.kind === "userMessage" ? entry.files : []
                            delegate: AttachmentPreview {
                                required property string modelData
                                Layout.fillWidth: true
                                filePath: modelData
                            }
                        }
                        Repeater {
                            model: entry.kind === "activity"
                                ? Array.from({length: entry.itemCount}, (_, i) => entry.startIndex + i)
                                    .filter(i => entry.expanded || i === Codex.liveCommandIndex) : []
                            delegate: ColumnLayout {
                                id: commandEntry
                                required property int modelData
                                readonly property var commandData: Codex.messages.get(modelData)
                                readonly property bool current: modelData === Codex.liveCommandIndex
                                readonly property bool running: current && commandData.status === "inProgress"
                                    && Codex.busy && !Codex.error && !Codex.interruptRequested
                                readonly property string label: commandData.kind === "fileChange"
                                    ? JSON.parse(commandData.files).join("\n") || qsTr("Modifiche ai file")
                                    : Codex.displayCommand(commandData.command) || qsTr("Command")
                                property bool expanded: false
                                Layout.fillWidth: true
                                spacing: 4
                                Button {
                                    id: commandToggle
                                    Layout.fillWidth: true
                                    background: Rectangle {
                                        color: "transparent"
                                        radius: Appearance.rounding.small
                                        border.width: commandToggle.visualFocus ? 1 : 0
                                        border.color: Appearance.colors.colPrimary
                                    }
                                    Accessible.name: commandEntry.label
                                    onClicked: {
                                        conversation.followOutput = false;
                                        commandEntry.expanded = !commandEntry.expanded;
                                    }
                                    contentItem: RowLayout {
                                        spacing: 8
                                        ActivitySpinner {
                                            visible: commandEntry.running
                                            Layout.preferredWidth: 16
                                            Layout.preferredHeight: 16
                                        }
                                        StyledText {
                                            Layout.fillWidth: true
                                            text: (commandEntry.expanded ? "▴ " : "▾ ")
                                                + commandEntry.label
                                                + (commandEntry.commandData.status ? " · " + commandEntry.commandData.status : "")
                                            textFormat: Text.PlainText
                                            wrapMode: Text.Wrap
                                            font.family: Appearance.font.family.monospace
                                            font.pixelSize: Appearance.font.pixelSize.small
                                        }
                                    }
                                }
                                TextEdit {
                                    Layout.fillWidth: true
                                    visible: commandEntry.expanded
                                    text: commandEntry.commandData.text
                                    textFormat: TextEdit.PlainText
                                    readOnly: true
                                    selectByMouse: true
                                    wrapMode: TextEdit.Wrap
                                    font.family: Appearance.font.family.monospace
                                    font.pixelSize: Appearance.font.pixelSize.small
                                    color: Appearance.colors.colOnLayer1
                                    Accessible.name: qsTr("Dettagli attività")
                                }
                            }
                        }
                    }
                }
            }

            StyledText {
                anchors.centerIn: parent
                width: parent.width - 24
                visible: Codex.messages.count === 0
                text: qsTr("Choose a project and describe the task. Codex can inspect code, run checks and propose changes.")
                wrapMode: Text.Wrap
                horizontalAlignment: Text.AlignHCenter
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 20
            readonly property bool active: Codex.thinking && Codex.busy && !Codex.error && !Codex.interruptRequested
            ActivitySpinner {
                visible: parent.active
                Layout.preferredWidth: 16
                Layout.preferredHeight: 16
            }
            StyledText {
                Layout.fillWidth: true
                text: "thinking"
                font.pixelSize: Appearance.font.pixelSize.smaller
                color: Appearance.colors.colSubtext
                opacity: parent.active ? 1 : 0
                Accessible.ignored: opacity === 0
            }
        }

        Repeater {
            model: Codex.approvals.slice(0, 1)
            delegate: ColumnLayout {
                id: approval
                required property var modelData
                Layout.fillWidth: true
                StyledText {
                    Layout.fillWidth: true
                    text: qsTr("Approval required")
                    color: Appearance.colors.colPrimary
                }
                ScrollView {
                    Layout.fillWidth: true
                    Layout.preferredHeight: Math.min(180, details.implicitHeight + 10)
                    clip: true
                    TextArea {
                        id: details
                        text: [approval.modelData.text, approval.modelData.cwd,
                            approval.modelData.command, approval.modelData.changes].filter(part => part).join("\n\n")
                        textFormat: TextEdit.PlainText
                        readOnly: true
                        selectByMouse: true
                        wrapMode: TextEdit.Wrap
                        color: Appearance.colors.colOnLayer0
                        Accessible.name: qsTr("Requested operation")
                    }
                }
                RowLayout {
                    DialogButton {
                        buttonText: qsTr("Reject")
                        onClicked: Codex.decide(approval.modelData.id, false)
                    }
                    DialogButton {
                        buttonText: qsTr("Approve once")
                        onClicked: Codex.decide(approval.modelData.id, true)
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            implicitHeight: composer.implicitHeight + 10
            radius: Appearance.rounding.normal - 4
            color: Appearance.colors.colLayer2
            clip: true

            ColumnLayout {
                id: composer
                anchors { left: parent.left; right: parent.right; top: parent.top; topMargin: 5 }
                spacing: 5
                ScrollView {
                    Layout.fillWidth: true
                    Layout.preferredHeight: Math.min(100, attachedFiles.implicitHeight)
                    Layout.leftMargin: 5
                    Layout.rightMargin: 5
                    visible: Codex.attachments.length > 0
                    contentWidth: availableWidth
                    clip: true
                    ColumnLayout {
                        id: attachedFiles
                        width: parent.width
                        spacing: 4
                        Repeater {
                            model: Codex.attachments
                            delegate: RowLayout {
                                id: attachedFile
                                required property string modelData
                                required property int index
                                Layout.fillWidth: true
                                AttachmentPreview {
                                    Layout.fillWidth: true
                                    filePath: attachedFile.modelData
                                    thumbnailSize: 40
                                }
                                DialogButton {
                                    buttonText: "×"
                                    implicitWidth: 32
                                    enabled: !Codex.busy
                                    Accessible.name: qsTr("Rimuovi %1").arg(attachedFile.modelData)
                                    onClicked: Codex.attachments = Codex.attachments.filter((path, index) => index !== attachedFile.index)
                                }
                            }
                        }
                    }
                }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 0
                    ScrollView {
                        Layout.fillWidth: true
                        Layout.preferredHeight: Math.min(140, Math.max(40, prompt.implicitHeight))
                        contentWidth: availableWidth
                        clip: true
                        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                        StyledTextArea {
                            id: prompt
                            placeholderText: qsTr("Scrivi a Codex…")
                            textFormat: TextEdit.PlainText
                            padding: 10
                            color: activeFocus ? Appearance.m3colors.m3onSurface : Appearance.m3colors.m3onSurfaceVariant
                            background: null
                            wrapMode: TextEdit.Wrap
                            selectByMouse: true
                            enabled: !Codex.busy
                            Accessible.name: qsTr("Message to Codex")
                            Keys.onReturnPressed: event => {
                                if (event.modifiers & Qt.ShiftModifier) { event.accepted = false; return; }
                                event.accepted = true;
                                root.submit();
                            }
                        }
                    }
                    RippleButton {
                        id: sendButton
                        Layout.alignment: Qt.AlignBottom
                        Layout.rightMargin: 5
                        implicitWidth: 40
                        implicitHeight: 40
                        buttonRadius: Appearance.rounding.small
                        enabled: Codex.busy || (Codex.ready && Codex.authenticated
                            && (prompt.text.trim().length > 0 || Codex.attachments.length > 0))
                        toggled: enabled
                        Accessible.name: Codex.busy ? qsTr("Interrompi") : qsTr("Invia")
                        ToolTip.visible: hovered
                        ToolTip.text: Codex.busy ? qsTr("Interrompi") : qsTr("Invio per inviare · Maiusc+Invio per andare a capo")
                        onClicked: Codex.busy ? Codex.stop() : root.submit()
                        contentItem: MaterialSymbol {
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            iconSize: 22
                            color: sendButton.enabled ? Appearance.m3colors.m3onPrimary : Appearance.colors.colOnLayer2Disabled
                            text: Codex.busy ? "stop" : "arrow_upward"
                        }
                    }
                }
                RowLayout {
                    Layout.fillWidth: true
                    Layout.leftMargin: 10
                    Layout.rightMargin: 5
                    spacing: 4
                    StyledComboBox {
                        id: modelSelector
                        Layout.fillWidth: false
                        Layout.preferredWidth: modelLabel.implicitWidth
                        Layout.preferredHeight: modelLabel.implicitHeight
                        padding: 0
                        enabled: !Codex.busy
                        indicator: null
                        background: Rectangle {
                            color: "transparent"
                            radius: Appearance.rounding.small
                            border.width: modelSelector.visualFocus ? 1 : 0
                            border.color: Appearance.colors.colPrimary
                        }
                        contentItem: ApiInputBoxIndicator {
                            id: modelLabel
                            icon: "api"
                            text: modelSelector.displayText
                        }
                        model: [{id: "", label: qsTr("Default model")}].concat(Codex.models.map(item => ({
                            id: item.model || item.id, label: item.displayName || item.model || item.id
                        })))
                        textRole: "label"
                        currentIndex: Math.max(0, model.findIndex(item => item.id === Config.options.ai.codex.model))
                        onActivated: Config.options.ai.codex.model = model[currentIndex].id
                        popup.width: Math.min(root.width - 32, 300)
                        popup.y: -popup.height - 4
                        Accessible.name: qsTr("Cambia modello Codex")
                        ToolTip.visible: hovered && !popup.visible
                        ToolTip.text: qsTr("Cambia modello Codex")
                        HoverHandler { cursorShape: Qt.PointingHandCursor }
                    }
                    StyledComboBox {
                        id: modeSelector
                        Layout.fillWidth: false
                        Layout.preferredWidth: modeLabel.implicitWidth
                        Layout.preferredHeight: modeLabel.implicitHeight
                        padding: 0
                        enabled: !Codex.busy
                        indicator: null
                        background: Rectangle {
                            color: "transparent"
                            radius: Appearance.rounding.small
                            border.width: modeSelector.visualFocus ? 1 : 0
                            border.color: Appearance.colors.colPrimary
                        }
                        contentItem: ApiInputBoxIndicator {
                            id: modeLabel
                            icon: "service_toolbox"
                            text: modeSelector.displayText
                        }
                        model: [{label: qsTr("Analyze"), edits: false}, {label: qsTr("Edit project"), edits: true}]
                        textRole: "label"
                        currentIndex: Config.options.ai.codex.allowEdits ? 1 : 0
                        onActivated: Config.options.ai.codex.allowEdits = model[currentIndex].edits
                        popup.width: Math.min(root.width - 32, 220)
                        popup.y: -popup.height - 4
                        Accessible.name: qsTr("Cambia modalità Codex")
                        ToolTip.visible: hovered && !popup.visible
                        ToolTip.text: qsTr("Cambia modalità Codex")
                        HoverHandler { cursorShape: Qt.PointingHandCursor }
                    }
                    Item { Layout.fillWidth: true }
                    RippleButton {
                        implicitWidth: 32
                        implicitHeight: 32
                        enabled: !Codex.busy
                        Accessible.name: qsTr("Allega file")
                        contentItem: MaterialSymbol {
                            text: "attach_file"
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            color: Appearance.colors.colPrimary
                        }
                        ToolTip.visible: hovered
                        ToolTip.text: qsTr("Allega file")
                        onClicked: {
                            Codex.fileDialogOpen = true;
                            Qt.callLater(() => attachmentPicker.open());
                        }
                    }
                }
            }
        }
    }

    function resetCountdown(resetsAt, now) {
        if (typeof resetsAt !== "number" || !Number.isFinite(resetsAt) || resetsAt <= 0) return qsTr("Reset non disponibile");
        const minutes = Math.ceil((resetsAt * 1000 - now) / 60000);
        if (minutes <= 0) return qsTr("Reset in aggiornamento…");
        const days = Math.floor(minutes / 1440);
        const hours = Math.floor(minutes / 60) % 24;
        const duration = days > 0 ? qsTr("%1g %2h").arg(days).arg(hours)
            : hours > 0 ? qsTr("%1h %2min").arg(hours).arg(minutes % 60) : qsTr("%1 min").arg(minutes);
        return qsTr("Reset tra %1").arg(duration);
    }

    function submit() {
        if (Codex.send(prompt.text)) {
            prompt.clear();
            conversation.followOutput = true;
        }
    }
}
