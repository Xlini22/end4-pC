pragma ComponentBehavior: Bound

import qs.modules.common
import QtQuick
import QtQuick.Layouts
import Quickshell.Wayland
import qs.services

Item {
    id: groupedList
    default property list<Item> items
    property real bigRadius: Appearance.rounding.normal
    property real smallRadius: Appearance.rounding.unsharpenmore
    property color bgcolor: Appearance.colors.colLayer1
    property real itemVerticalPadding: 24
    property bool glass: false
    readonly property Item glassViewport: {
        for (let item = parent; item; item = item.parent)
            if (item.settingsGlassViewport === true) return item
        return null
    }
    Layout.fillWidth: true
    implicitHeight: col.implicitHeight

    ColumnLayout {
        id: col
        anchors.fill: parent
        spacing: 2

        Repeater {
            model: groupedList.items.length
            delegate: Rectangle {
                required property int index
                readonly property bool collapsed: groupedList.items[index]?.groupedListCollapsed ?? false
                readonly property bool isFirst: index === 0
                readonly property bool isLast: index === groupedList.items.length - 1
                visible: !collapsed
                Layout.fillWidth: true
                implicitHeight: collapsed
                    ? 0
                    : (groupedList.items[index]?.implicitHeight ?? 0) + groupedList.itemVerticalPadding
                color: rowGlass.satinRow ? "transparent" : groupedList.bgcolor

                WindowGlass {
                    id: rowGlass
                    readonly property bool satinRow: !!groupedList.glassViewport && GlassCompositor.enhancedActive
                        && GlassCompositor.frostedAvailable && rowGlass.win?.WlrLayershell.namespace === "quickshell:settings"
                    anchors.fill: parent
                    glassEnabled: (groupedList?.glass ?? false) || rowGlass.satinRow
                    trackGeometry: !rowGlass.satinRow
                    nativeClip: rowGlass.satinRow ? groupedList.glassViewport : null
                    topLeftRadius: parent.topLeftRadius
                    topRightRadius: parent.topRightRadius
                    bottomLeftRadius: parent.bottomLeftRadius
                    bottomRightRadius: parent.bottomRightRadius
                    tint: groupedList?.bgcolor ?? "transparent"
                    frost: rowGlass.satinRow ? Math.max(8, Config.options.background.widgets.glass.haze) : 0
                }
                topLeftRadius:     isFirst ? groupedList.bigRadius : groupedList.smallRadius
                topRightRadius:    isFirst ? groupedList.bigRadius : groupedList.smallRadius
                bottomLeftRadius:  isLast  ? groupedList.bigRadius : groupedList.smallRadius
                bottomRightRadius: isLast  ? groupedList.bigRadius : groupedList.smallRadius

                Component.onCompleted: {
                    const child = groupedList.items[index]
                    if (child) {
                        child.parent = contentArea
                        child.Layout.fillWidth = true
                    }
                }

                ColumnLayout {
                    id: contentArea
                    anchors { fill: parent; margins: 8 }
                    spacing: 0
                }
            }
        }
    }
}
