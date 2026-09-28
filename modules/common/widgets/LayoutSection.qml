import qs.modules.common
import qs.modules.common.widgets
import qs.services
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls

ContentSubsection {
    id: root

    property string sectionTitle
    property var layout
    property var getWidgetName: (id) => id
    property var availableWidgets: []
    property var onUpdate: (list) => {}
    property var modeWidgets: []
    property var dynamicHoverModeWidgets: []
    property var widgetModes: ({})
    property var onModeChanged: (widget, mode) => {}
    property bool anchorControls: false
    property var rightAnchoredWidgets: []
    property var onAnchorChanged: (widget, anchor) => {}

    title: sectionTitle
    Layout.fillWidth: true
    Layout.leftMargin: 8
    Layout.topMargin: -4

    RowLayout {
        Layout.fillWidth: true
        spacing: 2

        Item {
            Layout.fillWidth: true
            implicitHeight: itemFlow.implicitHeight

            Flow {
                id: itemFlow
                anchors.fill: parent
                spacing: 2

                Repeater {
                    id: itemRepeater
                    model: root.layout

                    delegate: Rectangle {
                        id: widgetChip
                        required property var modelData
                        required property int index
                        readonly property bool hasModes: root.modeWidgets.includes(modelData)
                        readonly property bool hasDynamicHoverMode: root.dynamicHoverModeWidgets.includes(modelData)
                        readonly property bool hasControls: hasModes || root.anchorControls
                        implicitWidth: chipContent.implicitWidth + (hasControls ? 6 : 0)
                        implicitHeight: chipContent.implicitHeight
                        radius: height / 2
                        color: hasControls ? Appearance.colors.colPrimary : "transparent"

                        RowLayout {
                            id: chipContent
                            anchors.fill: parent
                            anchors.rightMargin: widgetChip.hasControls ? 6 : 0
                            spacing: 0

                            SelectionGroupButton {
                                isDragging: dragHandler.active
                                colBackgroundToggled: widgetChip.hasControls ? "transparent" : Appearance.colors.colPrimary
                                leftmost: true; rightmost: true
                                buttonIcon: "close"
                                buttonText: root.getWidgetName(modelData)
                                toggled: !dragHandler.active

                                DragHandler {
                                    id: dragHandler
                                    target: null

                                    function findNewIndex(dragX, dragY) {
                                        let newIndex = index
                                        let minDist = Infinity

                                        for (let i = 0; i < itemRepeater.count; i++) {
                                            if (i === index) continue
                                            const child = itemRepeater.itemAt(i)
                                            if (!child) continue
                                            const childCenter = child.mapToItem(null, child.width / 2, child.height / 2)
                                            const dx = dragX - childCenter.x
                                            const dy = dragY - childCenter.y
                                            const dist = Math.sqrt(dx * dx + dy * dy)
                                            if (dist < minDist) {
                                                minDist = dist
                                                newIndex = i
                                            }
                                        }
                                        return newIndex
                                    }

                                    onActiveChanged: {
                                        if (!active) {
                                            dropIndicator.visible = false
                                            dropIndicator.targetIndex = -1
                                            const dragX = dragHandler.centroid.scenePosition.x
                                            const dragY = dragHandler.centroid.scenePosition.y
                                            const newIndex = findNewIndex(dragX, dragY)
                                            if (newIndex !== index) {
                                                let list = root.layout.slice()
                                                const item = list.splice(index, 1)[0]
                                                list.splice(newIndex, 0, item)
                                                root.onUpdate(list)
                                            }
                                        }
                                    }

                                    onCentroidChanged: {
                                        if (!active) return
                                        const dragX = dragHandler.centroid.scenePosition.x
                                        const dragY = dragHandler.centroid.scenePosition.y
                                        const newIndex = findNewIndex(dragX, dragY)

                                        if (newIndex !== index) {
                                            const refChild = itemRepeater.itemAt(newIndex)
                                            if (refChild) {
                                                const refLocal = refChild.mapToItem(itemFlow, 0, 0)
                                                dropIndicator.x = newIndex < index
                                                    ? refLocal.x - 5
                                                    : refLocal.x + refChild.width + 1
                                                dropIndicator.y = refLocal.y
                                                dropIndicator.height = refChild.height
                                                dropIndicator.visible = true
                                                dropIndicator.targetIndex = newIndex
                                            }
                                        } else {
                                            dropIndicator.visible = false
                                            dropIndicator.targetIndex = -1
                                        }
                                    }
                                }

                                onClicked: {
                                    let list = root.layout.slice()
                                    list.splice(index, 1)
                                    root.onUpdate(list)
                                }
                            }
                            RowLayout {
                                visible: widgetChip.hasModes
                                spacing: 1
                                Repeater {
                                    model: widgetChip.hasDynamicHoverMode ? [
                                        { label: "D", mode: "dynamic", title: Translation.tr("Dynamic: expand with Dynamic Island") },
                                        { label: "DH", mode: "dynamicHover", title: Translation.tr("Dynamic hover: expand when hovering the component") },
                                        { label: "C", mode: "compact", title: Translation.tr("Always compact") },
                                        { label: "E", mode: "expanded", title: Translation.tr("Always expanded") }
                                    ] : [
                                        { label: "D", mode: "dynamic", title: Translation.tr("Dynamic: expand on hover") },
                                        { label: "C", mode: "compact", title: Translation.tr("Always compact") },
                                        { label: "E", mode: "expanded", title: Translation.tr("Always expanded") }
                                    ]
                                    delegate: SelectionGroupButton {
                                        required property var modelData
                                        buttonText: modelData.label
                                        contentItem: StyledText {
                                            text: parent.buttonText
                                            color: parent.colText
                                            horizontalAlignment: Text.AlignHCenter
                                            verticalAlignment: Text.AlignVCenter
                                        }
                                        horizontalPadding: 0
                                        verticalPadding: 0
                                        implicitWidth: 26
                                        implicitHeight: 26
                                        Layout.minimumWidth: 26
                                        Layout.maximumWidth: 26
                                        Layout.minimumHeight: 26
                                        Layout.maximumHeight: 26
                                        Layout.alignment: Qt.AlignVCenter
                                        Layout.fillWidth: false
                                        Layout.fillHeight: false
                                        leftRadius: 13
                                        rightRadius: 13
                                        colBackground: "transparent"
                                        colBackgroundHover: Appearance.colors.colPrimaryHover
                                        colBackgroundActive: Appearance.colors.colPrimaryActive
                                        colBackgroundToggled: Appearance.colors.colOnPrimary
                                        colBackgroundToggledHover: Appearance.colors.colOnPrimary
                                        colBackgroundToggledActive: Appearance.colors.colOnPrimary
                                        colText: toggled ? Appearance.colors.colPrimary : Appearance.colors.colOnPrimary
                                        leftmost: true
                                        rightmost: true
                                        toggled: (root.widgetModes[widgetChip.modelData] ?? "dynamic") === modelData.mode
                                        onClicked: root.onModeChanged(widgetChip.modelData, modelData.mode)
                                        StyledToolTip {
                                            text: parent.modelData.title
                                            delay: 400
                                        }
                                    }
                                }
                            }
                            Rectangle {
                                visible: root.anchorControls
                                Layout.leftMargin: 3
                                Layout.rightMargin: 3
                                Layout.alignment: Qt.AlignVCenter
                                implicitWidth: 1
                                implicitHeight: 16
                                radius: 1
                                color: Appearance.colors.colOnPrimary
                                opacity: 0.35
                            }
                            RowLayout {
                                visible: root.anchorControls
                                spacing: 1
                                Repeater {
                                    model: [
                                        { label: "L", anchor: "left", title: Translation.tr("Anchor to the left edge") },
                                        { label: "R", anchor: "right", title: Translation.tr("Anchor to the right edge") }
                                    ]
                                    delegate: SelectionGroupButton {
                                        required property var modelData
                                        buttonText: modelData.label
                                        contentItem: StyledText {
                                            text: parent.buttonText
                                            color: parent.colText
                                            horizontalAlignment: Text.AlignHCenter
                                            verticalAlignment: Text.AlignVCenter
                                        }
                                        horizontalPadding: 0
                                        verticalPadding: 0
                                        implicitWidth: 26
                                        implicitHeight: 26
                                        Layout.minimumWidth: 26
                                        Layout.maximumWidth: 26
                                        Layout.minimumHeight: 26
                                        Layout.maximumHeight: 26
                                        Layout.alignment: Qt.AlignVCenter
                                        Layout.fillWidth: false
                                        Layout.fillHeight: false
                                        leftRadius: 13
                                        rightRadius: 13
                                        colBackground: "transparent"
                                        colBackgroundHover: Appearance.colors.colPrimaryHover
                                        colBackgroundActive: Appearance.colors.colPrimaryActive
                                        colBackgroundToggled: Appearance.colors.colOnPrimary
                                        colBackgroundToggledHover: Appearance.colors.colOnPrimary
                                        colBackgroundToggledActive: Appearance.colors.colOnPrimary
                                        colText: toggled ? Appearance.colors.colPrimary : Appearance.colors.colOnPrimary
                                        leftmost: true
                                        rightmost: true
                                        toggled: modelData.anchor === "right"
                                            ? root.rightAnchoredWidgets.includes(widgetChip.modelData)
                                            : !root.rightAnchoredWidgets.includes(widgetChip.modelData)
                                        onClicked: root.onAnchorChanged(widgetChip.modelData, modelData.anchor)
                                        StyledToolTip {
                                            text: parent.modelData.title
                                            delay: 400
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            Rectangle {
                id: dropIndicator
                property int targetIndex: -1
                visible: false
                width: 3
                height: 32 
                radius: 2
                color: Appearance.colors.colPrimary

                Behavior on x { NumberAnimation { duration: 150; easing.type: Easing.OutCubic } }
                Behavior on y { NumberAnimation { duration: 150; easing.type: Easing.OutCubic } }
                Behavior on opacity { NumberAnimation { duration: 150 } }

                Rectangle {
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.top: parent.top
                    anchors.topMargin: -4
                    width: 8; height: 8; radius: 4
                    color: Appearance.colors.colPrimary
                }

                Rectangle {
                    anchors.horizontalCenter: parent.horizontalCentera
                    anchors.bottom: parent.bottom
                    anchors.bottomMargin: -4
                    width: 8; height: 8; radius: 4
                    color: Appearance.colors.colPrimary
                }
            }
        }

        ToolbarPairedFab {
            Layout.rightMargin: 8
            Layout.topMargin: -20
            Layout.alignment: Qt.AlignVCenter
            iconText: dropdown.dropdownOpen ? "keyboard_arrow_up" : "add"
            onClicked: dropdown.dropdownOpen = !dropdown.dropdownOpen
        }
    }

    Item {
        id: dropdown
        Layout.fillWidth: true
        Layout.topMargin: 5
        clip: true
        implicitHeight: dropdownOpen ? dropdownRect.implicitHeight + 8 : 0
        visible: implicitHeight > 0
        opacity: dropdownOpen ? 1 : 0

        property bool dropdownOpen: false

        Behavior on implicitHeight {
            NumberAnimation { duration: 200; easing.type: Easing.OutCubic }
        }
        Behavior on opacity {
            NumberAnimation { duration: 200; easing.type: Easing.OutCubic }
        }

        Rectangle {
            id: dropdownRect
            anchors.top: parent.top
            anchors.topMargin: 4
            width: parent.width
            implicitHeight: dropdownFlow.implicitHeight + 8
            color: "transparent"
            radius: Appearance.rounding.large

            Flow {
                id: dropdownFlow
                anchors { fill: parent; margins: 8 }
                spacing: 2
                Repeater {
                    model: root.availableWidgets
                    delegate: SelectionGroupButton {
                        required property var modelData
                        leftmost: true; rightmost: true
                        buttonText: modelData.name
                        buttonIcon: modelData.icon ?? ""  
                        onClicked: {
                            let list = root.layout.slice()
                            list.push(modelData.id)
                            root.onUpdate(list)
                            const keepOpen = ["visualizer", "divisor"]
                            if (!keepOpen.includes(modelData.id)) {
                                Qt.callLater(() => { dropdown.dropdownOpen = false })
                            }
                        }
                    }
                }
                StyledText {
                    visible: root.availableWidgets.length === 0
                    text: Translation.tr("No widgets available")
                    color: Appearance.colors.colSubtext
                    font.pixelSize: Appearance.font.pixelSize.small
                }
            }
        }
    }
}
